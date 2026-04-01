import argparse
import json
import os
import re
import sys
import textwrap
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

console = Console()

LEETCODE_CN_GRAPHQL = "https://leetcode.cn/graphql"
OPENAI_RESPONSES_API = "https://api.openai.com/v1/responses"
DIFFICULTY_ORDER = {"EASY": 0, "MEDIUM": 1, "HARD": 2}


def setup_utf8_output() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass


def choose_ui_lang(cli_value: Optional[str]) -> str:
    raw = (cli_value or os.getenv("UI_LANG", "auto")).strip().lower()
    if raw in {"zh", "cn", "en"}:
        return "zh" if raw == "cn" else raw
    enc = (sys.stdout.encoding or "").lower()
    return "zh" if "utf" in enc else "en"


def tr(zh: str, en: str, ui_lang: str) -> str:
    return zh if ui_lang in {"zh", "cn"} else en


@dataclass
class Problem:
    frontend_id: str
    title: str
    title_slug: str
    difficulty: str
    paid_only: bool
    status: Optional[str]
    topic_tags: List[str]


class LeetCodeClient:
    def __init__(self, cookie: str):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0",
                "Referer": "https://leetcode.cn/problemset/",
                "Content-Type": "application/json",
                "Cookie": cookie,
            }
        )

    def _post_graphql(self, query: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        resp = self.session.post(
            LEETCODE_CN_GRAPHQL,
            json={"query": query, "variables": variables},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        if "errors" in data:
            raise RuntimeError(f"GraphQL errors: {data['errors']}")
        return data["data"]

    def fetch_problemset(self, limit: int = 50, skip: int = 0) -> List[Problem]:
        query = """
        query problemsetQuestionList($categorySlug: String, $limit: Int, $skip: Int, $filters: QuestionListFilterInput) {
          problemsetQuestionList(categorySlug: $categorySlug, limit: $limit, skip: $skip, filters: $filters) {
            questions {
              frontendQuestionId
              title
              titleSlug
              difficulty
              paidOnly
              status
              topicTags {
                slug
              }
            }
          }
        }
        """
        variables = {
            "categorySlug": "all-code-essentials",
            "skip": skip,
            "limit": limit,
            "filters": {},
        }

        data = self._post_graphql(query, variables)
        questions = data["problemsetQuestionList"]["questions"]
        return [
            Problem(
                frontend_id=q["frontendQuestionId"],
                title=q["title"],
                title_slug=q["titleSlug"],
                difficulty=q["difficulty"],
                paid_only=q["paidOnly"],
                status=q.get("status"),
                topic_tags=[t["slug"] for t in (q.get("topicTags") or [])],
            )
            for q in questions
        ]

    def fetch_problem_detail(self, title_slug: str) -> Dict[str, Any]:
        query = """
        query questionData($titleSlug: String!) {
          question(titleSlug: $titleSlug) {
            questionId
            questionFrontendId
            title
            titleSlug
            difficulty
            translatedTitle
            translatedContent
            content
            sampleTestCase
            topicTags {
              name
              slug
            }
            codeSnippets {
              lang
              langSlug
              code
            }
          }
        }
        """
        data = self._post_graphql(query, {"titleSlug": title_slug})
        question = data.get("question") or {}
        if not question:
            raise RuntimeError("Failed to fetch problem detail")
        return question

    def check_auth(self) -> Dict[str, Any]:
        query = """
        query globalData {
          userStatus {
            isSignedIn
            username
            realName
          }
        }
        """
        data = self._post_graphql(query, {})
        return data.get("userStatus") or {}


class AIClient:
    def __init__(self, api_key: str, model: str, provider: str = "openai", base_url: str = None):
        self.api_key = api_key
        self.model = model
        self.provider = provider.lower()
        self.base_url = base_url
        
        # 设置不同供应商的默认基础URL
        if not self.base_url:
            if self.provider == "openai":
                self.base_url = "https://api.openai.com/v1"
            elif self.provider == "deepseek":
                self.base_url = "https://api.deepseek.com/v1"
            elif self.provider == "gemini":
                self.base_url = "https://generativelanguage.googleapis.com/v1beta"
            elif self.provider == "claude":
                self.base_url = "https://api.anthropic.com/v1"
            else:
                self.base_url = "https://api.openai.com/v1"  # 默认

    def generate_best_solution(self, detail: Dict[str, Any], lang: str, compare: bool = False) -> Dict[str, Any]:
        content = detail.get("translatedContent") or detail.get("content") or ""
        samples = detail.get("sampleTestCase") or ""
        tags = ", ".join([t.get("slug", "") for t in (detail.get("topicTags") or []) if t.get("slug")])

        if compare:
            system_prompt = (
                "You are an algorithm interview coach. Provide 2-3 feasible solutions with comparison "
                "focusing on time/space complexity, implementation difficulty, and interview suitability. "
                "Be concise and accurate."
            )
            user_prompt = f"""
Problem: {detail.get('translatedTitle') or detail.get('title')}
Slug: {detail.get('titleSlug')}
Difficulty: {detail.get('difficulty')}
Tags: {tags}
Language target: {lang}

Problem statement (may contain HTML):
{content}

Sample test case text:
{samples}

Required output sections in markdown:
## 1. Solution Comparison Table
Present 2-3 different approaches in a table with columns:
- Approach (brief name)
- Time Complexity (best/average/worst)
- Space Complexity
- Implementation Difficulty (Low/Medium/High)
- Interview Recommendation (1-5 stars)
- When to choose (short scenario)

## 2. Detailed Analysis
For each approach:
- Core idea
- Step-by-step reasoning
- Why this time/space complexity is optimal (or lower bound)
- Key trade-offs

## 3. Recommended Solution for Interview
Select the most appropriate solution for interview context and explain:
- Why it's preferred (balance of complexity, readability, interview frequency)
- Common pitfalls to avoid
- How to derive it during an interview

## 4. Edge Cases Checklist
- List 5-7 most common edge cases and mistakes

## 5. Reference Implementation ({lang})
- Clean, production-ready code for the recommended solution
- Include comments for key steps

## 6. Custom Test Cases
- 3 custom tests covering typical and edge scenarios

Important:
- Focus on interview context: what candidates are expected to explain.
- If multiple approaches have same time complexity, compare readability and corner case handling.
- Provide honest trade-offs, not just the theoretically optimal one.
"""
        else:
            system_prompt = (
                "You are an algorithm mentor. Return a minimum-time-complexity-first reference solution "
                "for learning. Be concise and accurate."
            )
            user_prompt = f"""
Problem: {detail.get('translatedTitle') or detail.get('title')}
Slug: {detail.get('titleSlug')}
Difficulty: {detail.get('difficulty')}
Tags: {tags}
Language target: {lang}

Problem statement (may contain HTML):
{content}

Sample test case text:
{samples}

Required output sections in markdown:
1) Best strategy summary (why likely minimal time complexity)
2) Time/space complexity with short proof
3) Edge cases checklist
4) Final reference code ({lang})
5) 3 custom tests

Important:
- Prefer minimal time complexity first, then lower space and simpler implementation.
- If multiple strategies tie in time complexity, choose the cleaner one and explain.
- This is study reference, not guaranteed absolute theoretical optimum.
"""

        # 根据供应商构建不同的请求
        if self.provider in ["openai", "deepseek"]:
            # OpenAI兼容格式
            body = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 4000
            }
            
            endpoint = f"{self.base_url}/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            
        elif self.provider == "gemini":
            # Google Gemini格式
            body = {
                "contents": [
                    {
                        "parts": [
                            {"text": system_prompt + "\n\n" + user_prompt}
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.3,
                    "maxOutputTokens": 4000,
                }
            }
            
            endpoint = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"
            headers = {"Content-Type": "application/json"}
            
        elif self.provider == "claude":
            # Anthropic Claude格式
            body = {
                "model": self.model,
                "max_tokens": 4000,
                "temperature": 0.3,
                "messages": [
                    {"role": "user", "content": system_prompt + "\n\n" + user_prompt}
                ]
            }
            
            endpoint = f"{self.base_url}/messages"
            headers = {
                "x-api-key": self.api_key,
                "anthropic-version": "2025-10-01",  # 更新为支持Claude 4系列的版本
                "Content-Type": "application/json",
            }
            
        else:
            # 默认使用OpenAI兼容格式
            body = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 4000
            }
            
            endpoint = f"{self.base_url}/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

        resp = requests.post(
            endpoint,
            headers=headers,
            json=body,
            timeout=90,
        )
        resp.raise_for_status()
        data = resp.json()

        # 解析不同供应商的响应
        if self.provider in ["openai", "deepseek"]:
            text = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            input_tokens = usage.get("prompt_tokens", 0)
            output_tokens = usage.get("completion_tokens", 0)
            
        elif self.provider == "gemini":
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            usage = data.get("usageMetadata", {})
            input_tokens = usage.get("promptTokenCount", 0)
            output_tokens = usage.get("candidatesTokenCount", 0)
            
        elif self.provider == "claude":
            text = data["content"][0]["text"]
            usage = data.get("usage", {})
            input_tokens = usage.get("input_tokens", 0)
            output_tokens = usage.get("output_tokens", 0)
            
        else:
            # 默认OpenAI兼容格式
            text = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            input_tokens = usage.get("prompt_tokens", 0)
            output_tokens = usage.get("completion_tokens", 0)

        return {
            "text": text,
            "input_tokens": int(input_tokens),
            "output_tokens": int(output_tokens),
            "model": self.model,
            "provider": self.provider,
        }

    def generate_text(self, system_prompt: str, user_prompt: str, max_output_tokens: int = 2000) -> Dict[str, Any]:
        if self.provider in ["openai", "deepseek"]:
            body = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.3,
                "max_tokens": max_output_tokens,
            }
            endpoint = f"{self.base_url}/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
        elif self.provider == "gemini":
            body = {
                "contents": [{"parts": [{"text": system_prompt + "\n\n" + user_prompt}]}],
                "generationConfig": {
                    "temperature": 0.3,
                    "maxOutputTokens": max_output_tokens,
                },
            }
            endpoint = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"
            headers = {"Content-Type": "application/json"}
        elif self.provider == "claude":
            body = {
                "model": self.model,
                "max_tokens": max_output_tokens,
                "temperature": 0.3,
                "messages": [{"role": "user", "content": system_prompt + "\n\n" + user_prompt}],
            }
            endpoint = f"{self.base_url}/messages"
            headers = {
                "x-api-key": self.api_key,
                "anthropic-version": "2025-10-01",
                "Content-Type": "application/json",
            }
        else:
            body = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.3,
                "max_tokens": max_output_tokens,
            }
            endpoint = f"{self.base_url}/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

        resp = requests.post(endpoint, headers=headers, json=body, timeout=90)
        resp.raise_for_status()
        data = resp.json()

        if self.provider in ["openai", "deepseek"]:
            text = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            input_tokens = usage.get("prompt_tokens", 0)
            output_tokens = usage.get("completion_tokens", 0)
        elif self.provider == "gemini":
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            usage = data.get("usageMetadata", {})
            input_tokens = usage.get("promptTokenCount", 0)
            output_tokens = usage.get("candidatesTokenCount", 0)
        elif self.provider == "claude":
            text = data["content"][0]["text"]
            usage = data.get("usage", {})
            input_tokens = usage.get("input_tokens", 0)
            output_tokens = usage.get("output_tokens", 0)
        else:
            text = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            input_tokens = usage.get("prompt_tokens", 0)
            output_tokens = usage.get("completion_tokens", 0)

        return {
            "text": text,
            "input_tokens": int(input_tokens),
            "output_tokens": int(output_tokens),
            "model": self.model,
            "provider": self.provider,
        }


def resolve_ai_settings(args: argparse.Namespace) -> Dict[str, str]:
    provider = (args.provider or os.getenv("AI_PROVIDER", "openai")).strip().lower()
    model_env_map = {
        "openai": "OPENAI_MODEL",
        "deepseek": "DEEPSEEK_MODEL",
        "gemini": "GEMINI_MODEL",
        "claude": "CLAUDE_MODEL",
    }
    key_env_map = {
        "openai": "OPENAI_API_KEY",
        "deepseek": "DEEPSEEK_API_KEY",
        "gemini": "GEMINI_API_KEY",
        "claude": "CLAUDE_API_KEY",
    }

    model = (args.model or os.getenv(model_env_map.get(provider, "OPENAI_MODEL"), "gpt-5.3")).strip()
    api_key = (args.api_key or os.getenv(key_env_map.get(provider, "OPENAI_API_KEY"), "")).strip()
    base_url = (args.base_url or os.getenv("AI_BASE_URL") or "").strip() or None

    if not api_key:
        raise RuntimeError(f"{provider.upper()}_API_KEY is missing. Set env or pass --api-key")

    return {
        "provider": provider,
        "model": model,
        "api_key": api_key,
        "base_url": base_url or "",
    }


def problem_context(detail: Dict[str, Any]) -> Dict[str, str]:
    return {
        "title": detail.get("translatedTitle") or detail.get("title") or "",
        "slug": detail.get("titleSlug") or "",
        "difficulty": detail.get("difficulty") or "",
        "tags": ", ".join([t.get("slug", "") for t in (detail.get("topicTags") or []) if t.get("slug")]),
        "content": detail.get("translatedContent") or detail.get("content") or "",
        "samples": detail.get("sampleTestCase") or "",
    }


def build_ai_feedback_prompts(detail: Dict[str, Any], user_code: str, lang: str) -> Dict[str, str]:
    ctx = problem_context(detail)
    system_prompt = (
        "You are an algorithm interview coach. The user has written code for a problem but it contains errors. "
        "Identify the single most important logical issue, give a correction direction, and avoid writing the full final solution."
    )
    user_prompt = f"""
Problem: {ctx['title']}
Slug: {ctx['slug']}
Difficulty: {ctx['difficulty']}
Tags: {ctx['tags']}

Problem statement (may contain HTML):
{ctx['content']}

User's code:
```{lang}
{user_code}
```

Provide feedback in the following format:
## 1. Critical Error
- Identify the single most important logical error
- Explain why it breaks correctness or misses constraints

## 2. Correction Direction
- Suggest one concrete next step to fix it
- Do NOT write the corrected final code

## 3. Common Pitfall Reminder
- Mention one edge case the user should test after the fix

Keep the response under 300 words. Act like an interviewer giving a strong hint.
"""
    return {"system": system_prompt, "user": user_prompt}


def build_interview_eval_prompts(detail: Dict[str, Any], user_code: str, lang: str) -> Dict[str, str]:
    ctx = problem_context(detail)
    system_prompt = (
        "You are a senior engineer conducting a technical interview at a top-tier tech company in China and globally. "
        "Evaluate the candidate using standards common to ByteDance, Tencent, Alibaba, Huawei, Google, Amazon, Meta, and Microsoft. "
        "Focus on algorithm correctness, complexity, code clarity, edge cases, and communication quality. "
        "Provide a clear PASS or FAIL with concise justification."
    )
    user_prompt = f"""
Problem: {ctx['title']}
Slug: {ctx['slug']}
Difficulty: {ctx['difficulty']}
Tags: {ctx['tags']}

Problem statement (may contain HTML):
{ctx['content']}

User's code:
```{lang}
{user_code}
```

Evaluate this solution on the following dimensions (1-5 points each):
1. Algorithm Correctness
2. Time Complexity
3. Space Complexity
4. Code Readability
5. Edge Case Handling
6. Code Style
7. Problem-Solving Communication

Return markdown in this structure:
## Interview Evaluation Result

### Overall Decision
- **PASS** or **FAIL**

### Score Summary (1-5 each)
- Algorithm Correctness: X/5
- Time Complexity: X/5
- Space Complexity: X/5
- Code Readability: X/5
- Edge Case Handling: X/5
- Code Style: X/5
- Problem-Solving Communication: X/5

### Detailed Feedback
- **Strengths**: 1-3 concise points
- **Weaknesses**: 1-3 concise points
- **Improvement Suggestions**: concrete next actions

### Interviewer's Notes
- Briefly simulate what the interviewer would say
- State whether this would support a hire recommendation

Keep the response around 400-500 words.
"""
    return {"system": system_prompt, "user": user_prompt}


def load_config() -> Dict[str, Any]:
    with open("config.json", "r", encoding="utf-8") as f:
        return json.load(f)


def ensure_dirs(cfg: Dict[str, Any]) -> None:
    ws = cfg["workspace"]
    for k in ["plans_dir", "solutions_dir", "tests_dir", "logs_dir"]:
        Path(ws[k]).mkdir(parents=True, exist_ok=True)


def filter_unsolved(problems: List[Problem]) -> List[Problem]:
    return [p for p in problems if p.status != "ac"]


def apply_filters(problems: List[Problem], difficulty: Optional[List[str]], tags: Optional[List[str]]) -> List[Problem]:
    result = problems
    if difficulty:
        allow = {d.upper() for d in difficulty}
        result = [p for p in result if p.difficulty.upper() in allow]
    if tags:
        tag_set = {t.strip().lower() for t in tags if t.strip()}
        result = [p for p in result if tag_set.intersection(set(p.topic_tags))]
    return result


def parse_frontend_id(frontend_id: str) -> int:
    try:
        return int(frontend_id)
    except ValueError:
        return 10**9


def sanitize_name(s: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]", "_", s)


def recommend_problem(problems: List[Problem]) -> Problem:
    return sorted(
        problems,
        key=lambda p: (
            DIFFICULTY_ORDER.get(p.difficulty.upper(), 99),
            parse_frontend_id(p.frontend_id),
            p.title_slug,
        ),
    )[0]


def print_problem_table(problems: List[Problem], ui_lang: str) -> None:
    t = Table(title=tr("未完成题目（筛选后）", "Unsolved Problems (Filtered)", ui_lang))
    t.add_column("#")
    t.add_column("ID")
    t.add_column(tr("标题", "Title", ui_lang))
    t.add_column(tr("难度", "Difficulty", ui_lang))
    t.add_column(tr("标签", "Tags", ui_lang))
    for i, p in enumerate(problems, start=1):
        t.add_row(str(i), p.frontend_id, p.title, p.difficulty, ",".join(p.topic_tags[:4]))
    console.print(t)


def choose_problem(problems: List[Problem], idx: Optional[int], ui_lang: str) -> Problem:
    if idx is None:
        idx = int(console.input(tr("请输入序号（#）: ", "Enter row number (#): ", ui_lang)))
    if idx < 1 or idx > len(problems):
        raise ValueError(tr("序号超出范围", "Row number out of range", ui_lang))
    return problems[idx - 1]


def append_log(cfg: Dict[str, Any], record: Dict[str, Any]) -> str:
    log_file = Path(cfg["workspace"]["logs_dir"]) / "practice_log.jsonl"
    with log_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return str(log_file)


def open_problem_page(problem: Problem, ui_lang: str) -> None:
    url = f"https://leetcode.cn/problems/{problem.title_slug}/"
    try:
        import webbrowser

        webbrowser.open(url)
    except Exception as e:
        console.print(tr(f"[yellow]打开浏览器失败：{e}[/yellow]", f"[yellow]Failed to open browser: {e}[/yellow]", ui_lang))


def maybe_open_problem(args: argparse.Namespace, problem: Problem, ui_lang: str) -> None:
    if args.open:
        ans = console.input(tr("打开题目页面？(y/N): ", "Open problem page? (y/N): ", ui_lang)).strip().lower()
        if ans in {"y", "yes"}:
            open_problem_page(problem, ui_lang)


def write_simple_files(cfg: Dict[str, Any], problem: Problem, lang: str, prefix: str = "") -> Dict[str, str]:
    ws = cfg["workspace"]
    base = f"{problem.frontend_id}_{sanitize_name(problem.title_slug)}"
    plan = Path(ws["plans_dir"]) / f"{prefix}{base}.md"
    sol = Path(ws["solutions_dir"]) / f"{prefix}{base}.py"
    test = Path(ws["tests_dir"]) / f"test_{prefix}{base}.py"

    # Load template if available
    template_content = ""
    template_path = Path("templates.json")
    if template_path.exists():
        try:
            import json
            with open(template_path, "r", encoding="utf-8") as f:
                templates = json.load(f)
            # Find first matching tag
            for tag in problem.topic_tags:
                if tag in templates:
                    template_content = "\n\n" + templates[tag]
                    break
        except Exception:
            pass  # Silently ignore template errors
    
    plan.write_text(f"# {problem.frontend_id}. {problem.title}\n\n- slug: {problem.title_slug}\n{template_content}", encoding="utf-8")
    sol.write_text(
        textwrap.dedent(
            f"""\
            # {problem.frontend_id}. {problem.title}
            # URL: https://leetcode.cn/problems/{problem.title_slug}/
            class Solution:
                def solve(self, *args, **kwargs):
                    pass
            """
        ),
        encoding="utf-8",
    )
    test.write_text("def test_placeholder():\n    assert True\n", encoding="utf-8")
    return {"plan": str(plan), "solution": str(sol), "test": str(test)}


def budget_file(cfg: Dict[str, Any]) -> Path:
    return Path(cfg["workspace"]["logs_dir"]) / "ai_budget.json"


def _period_start(period: str, now: datetime) -> str:
    if period == "monthly":
        return now.strftime("%Y-%m-01")
    return now.strftime("%Y-%m-%d")


def _new_budget_from_config(cfg: Dict[str, Any]) -> Dict[str, Any]:
    ai_cfg = cfg.get("ai", {})
    b_cfg = ai_cfg.get("budget", {})
    now = datetime.now()
    reset_period = b_cfg.get("reset_period", "daily")
    return {
        "max_calls": int(b_cfg.get("max_calls", 20)),
        "max_input_tokens": int(b_cfg.get("max_input_tokens", 200000)),
        "max_output_tokens": int(b_cfg.get("max_output_tokens", 200000)),
        "reset_period": reset_period,
        "period_start": _period_start(reset_period, now),
        "used_calls": 0,
        "used_input_tokens": 0,
        "used_output_tokens": 0,
        "updated_at": now.isoformat(timespec="seconds"),
    }


def load_budget(cfg: Dict[str, Any]) -> Dict[str, Any]:
    path = budget_file(cfg)
    if path.exists():
        budget = json.loads(path.read_text(encoding="utf-8"))
    else:
        budget = _new_budget_from_config(cfg)

    budget.setdefault("reset_period", cfg.get("ai", {}).get("budget", {}).get("reset_period", "daily"))
    budget.setdefault("period_start", _period_start(budget["reset_period"], datetime.now()))
    budget.setdefault("max_calls", int(cfg.get("ai", {}).get("budget", {}).get("max_calls", 20)))
    budget.setdefault("max_input_tokens", int(cfg.get("ai", {}).get("budget", {}).get("max_input_tokens", 200000)))
    budget.setdefault("max_output_tokens", int(cfg.get("ai", {}).get("budget", {}).get("max_output_tokens", 200000)))
    budget.setdefault("used_calls", 0)
    budget.setdefault("used_input_tokens", 0)
    budget.setdefault("used_output_tokens", 0)

    maybe_reset_budget_period(budget)
    return budget


def save_budget(cfg: Dict[str, Any], budget: Dict[str, Any]) -> None:
    budget["updated_at"] = datetime.now().isoformat(timespec="seconds")
    budget_file(cfg).write_text(json.dumps(budget, ensure_ascii=False, indent=2), encoding="utf-8")


def maybe_reset_budget_period(budget: Dict[str, Any]) -> bool:
    now = datetime.now()
    expected = _period_start(budget.get("reset_period", "daily"), now)
    if budget.get("period_start") != expected:
        budget["period_start"] = expected
        budget["used_calls"] = 0
        budget["used_input_tokens"] = 0
        budget["used_output_tokens"] = 0
        budget["updated_at"] = now.isoformat(timespec="seconds")
        return True
    return False


def budget_remaining(budget: Dict[str, Any]) -> Dict[str, int]:
    return {
        "calls": max(0, int(budget["max_calls"]) - int(budget["used_calls"])),
        "input_tokens": max(0, int(budget["max_input_tokens"]) - int(budget["used_input_tokens"])),
        "output_tokens": max(0, int(budget["max_output_tokens"]) - int(budget["used_output_tokens"])),
    }


def budget_check(budget: Dict[str, Any]) -> Optional[str]:
    if budget["used_calls"] >= budget["max_calls"]:
        return "call_limit"
    if budget["used_input_tokens"] >= budget["max_input_tokens"]:
        return "input_token_limit"
    if budget["used_output_tokens"] >= budget["max_output_tokens"]:
        return "output_token_limit"
    return None


def estimate_tokens_for_prompt(problem_detail: Dict[str, Any], compare: bool = False) -> Dict[str, int]:
    content = (problem_detail.get("translatedContent") or problem_detail.get("content") or "")
    samples = (problem_detail.get("sampleTestCase") or "")
    title = f"{problem_detail.get('title', '')} {problem_detail.get('translatedTitle', '')}"
    raw_text = f"{title}\n{content}\n{samples}"
    # rough estimate: 1 token ~= 4 chars for mixed text/code
    est_input = max(500, len(raw_text) // 4 + 300)
    est_output = 1600
    if compare:
        # Multi-solution comparison requires more output
        est_output = int(est_output * 1.5)  # ~2400 tokens
    return {"input_tokens": est_input, "output_tokens": est_output}


def estimate_tokens_for_text(system_prompt: str, user_prompt: str, max_output_tokens: int = 2000) -> Dict[str, int]:
    raw_text = f"{system_prompt}\n{user_prompt}"
    est_input = max(500, len(raw_text) // 4 + 200)
    return {"input_tokens": est_input, "output_tokens": max_output_tokens}


def update_budget_after_call(budget: Dict[str, Any], input_tokens: int, output_tokens: int) -> None:
    budget["used_calls"] += 1
    budget["used_input_tokens"] += input_tokens
    budget["used_output_tokens"] += output_tokens


def print_budget_summary(budget: Dict[str, Any], ui_lang: str) -> None:
    rem = budget_remaining(budget)
    console.print(
        tr(
            f"[cyan]预算窗口: {budget['reset_period']} | 起始: {budget['period_start']}[/cyan]",
            f"[cyan]Budget window: {budget['reset_period']} | start: {budget['period_start']}[/cyan]",
            ui_lang,
        )
    )
    console.print(
        tr(
            f"[cyan]Calls: {budget['used_calls']}/{budget['max_calls']} (剩余 {rem['calls']})[/cyan]",
            f"[cyan]Calls: {budget['used_calls']}/{budget['max_calls']} (remaining {rem['calls']})[/cyan]",
            ui_lang,
        )
    )
    console.print(
        tr(
            f"[cyan]Input tokens: {budget['used_input_tokens']}/{budget['max_input_tokens']} (剩余 {rem['input_tokens']})[/cyan]",
            f"[cyan]Input tokens: {budget['used_input_tokens']}/{budget['max_input_tokens']} (remaining {rem['input_tokens']})[/cyan]",
            ui_lang,
        )
    )
    console.print(
        tr(
            f"[cyan]Output tokens: {budget['used_output_tokens']}/{budget['max_output_tokens']} (剩余 {rem['output_tokens']})[/cyan]",
            f"[cyan]Output tokens: {budget['used_output_tokens']}/{budget['max_output_tokens']} (remaining {rem['output_tokens']})[/cyan]",
            ui_lang,
        )
    )


def write_ai_solution_files(cfg: Dict[str, Any], problem: Problem, ai_markdown: str) -> Dict[str, str]:
    ws = cfg["workspace"]
    base = f"{problem.frontend_id}_{sanitize_name(problem.title_slug)}"
    note = Path(ws["plans_dir"]) / f"ai_fallback_{base}.md"
    sol = Path(ws["solutions_dir"]) / f"ai_fallback_{base}.md"
    note.write_text(ai_markdown, encoding="utf-8")
    sol.write_text(ai_markdown, encoding="utf-8")
    return {"ai_note": str(note), "ai_solution_markdown": str(sol)}


def write_ai_report_file(cfg: Dict[str, Any], problem_slug: str, prefix: str, markdown: str) -> str:
    report_path = Path(cfg["workspace"]["plans_dir"]) / f"{prefix}_{sanitize_name(problem_slug)}.md"
    report_path.write_text(markdown, encoding="utf-8")
    return str(report_path)


def main() -> None:
    load_dotenv()
    setup_utf8_output()

    parser = argparse.ArgumentParser(description="LeetCode learning helper")
    parser.add_argument(
        "command",
        choices=[
            "list",
            "prepare",
            "recommend",
            "fallback-solve",
            "ai-fallback",
            "ai-feedback",
            "ai-interview-eval",
            "set-ai-budget",
            "show-ai-budget",
            "estimate-ai-fallback",
            "check-auth",
            "log",
        ],
        help="command",
    )
    parser.add_argument("--difficulty", default="")
    parser.add_argument("--tags", default="")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--pick", type=int, default=None)
    parser.add_argument("--lang", default=None)
    parser.add_argument("--open", action="store_true")
    parser.add_argument("--pass-rate", type=float, default=None)
    parser.add_argument("--spent-min", type=float, default=None)
    parser.add_argument("--cause", default="")
    parser.add_argument("--ui-lang", default=None)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--compare", action="store_true", help="output multiple solutions comparison for interview training")
    parser.add_argument("--code", default=None, help="path to user's code file for feedback")
    parser.add_argument("--slug", default=None, help="problem title slug (e.g., two-sum)")
    parser.add_argument("--api-key", default=None)
    parser.add_argument("--model", default=None)
    parser.add_argument("--provider", default="openai", help="AI provider: openai, deepseek, gemini, claude, custom")
    parser.add_argument("--base-url", default=None, help="Custom API base URL")
    parser.add_argument("--max-calls", type=int, default=None)
    parser.add_argument("--max-input-tokens", type=int, default=None)
    parser.add_argument("--max-output-tokens", type=int, default=None)
    parser.add_argument("--reset-period", default=None, help="budget reset period: daily/monthly")
    parser.add_argument("--no-estimate", action="store_true", help="skip pre-call token estimate prompt")
    args = parser.parse_args()

    ui_lang = choose_ui_lang(args.ui_lang)
    cfg = load_config()
    ensure_dirs(cfg)

    if args.command == "ai-feedback":
        if not args.code or not args.slug:
            raise RuntimeError("Both --code and --slug are required for ai-feedback")
        code_path = Path(args.code)
        if not code_path.exists():
            raise RuntimeError(f"Code file not found: {code_path}")
        user_code = code_path.read_text(encoding="utf-8").strip()

        cookie = os.getenv("LEETCODE_COOKIE", "").strip()
        if not cookie:
            raise RuntimeError(tr("鏈娴嬪埌 LEETCODE_COOKIE", "LEETCODE_COOKIE is missing", ui_lang))
        client = LeetCodeClient(cookie)
        detail = client.fetch_problem_detail(args.slug)

        settings = resolve_ai_settings(args)
        prompts = build_ai_feedback_prompts(detail, user_code, args.lang or "python3")
        budget = load_budget(cfg)
        if maybe_reset_budget_period(budget):
            save_budget(cfg, budget)
        blocked = budget_check(budget)
        if blocked:
            raise RuntimeError(f"AI budget exceeded: {blocked}. Use set-ai-budget to adjust limits.")

        estimate = estimate_tokens_for_text(prompts["system"], prompts["user"], max_output_tokens=1200)
        rem = budget_remaining(budget)
        if (
            estimate["input_tokens"] > rem["input_tokens"]
            or estimate["output_tokens"] > rem["output_tokens"]
            or rem["calls"] < 1
        ):
            console.print("[yellow]AI feedback may exceed remaining budget[/yellow]")

        try:
            ai_client = AIClient(
                api_key=settings["api_key"],
                model=settings["model"],
                provider=settings["provider"],
                base_url=settings["base_url"] or None,
            )
            result = ai_client.generate_text(prompts["system"], prompts["user"], max_output_tokens=1200)
            update_budget_after_call(budget, result["input_tokens"], result["output_tokens"])
            save_budget(cfg, budget)

            report_path = write_ai_report_file(cfg, args.slug, "ai_feedback", result["text"])
            console.print("[green]AI Feedback:[/green]")
            console.print(result["text"])
            console.print(f"- report: {report_path}")
            append_log(
                cfg,
                {
                    "timestamp": datetime.now().isoformat(timespec="seconds"),
                    "action": "ai_feedback",
                    "slug": args.slug,
                    "provider": result["provider"],
                    "model": result["model"],
                    "input_tokens": result["input_tokens"],
                    "output_tokens": result["output_tokens"],
                    "report_path": report_path,
                },
            )
        except Exception as e:
            console.print(f"[red]AI feedback failed: {e}[/red]")
        return

    if args.command == "ai-interview-eval":
        if not args.code or not args.slug:
            raise RuntimeError("Both --code and --slug are required for ai-interview-eval")
        code_path = Path(args.code)
        if not code_path.exists():
            raise RuntimeError(f"Code file not found: {code_path}")
        user_code = code_path.read_text(encoding="utf-8").strip()

        cookie = os.getenv("LEETCODE_COOKIE", "").strip()
        if not cookie:
            raise RuntimeError(tr("鏈娴嬪埌 LEETCODE_COOKIE", "LEETCODE_COOKIE is missing", ui_lang))
        client = LeetCodeClient(cookie)
        detail = client.fetch_problem_detail(args.slug)

        settings = resolve_ai_settings(args)
        prompts = build_interview_eval_prompts(detail, user_code, args.lang or "python3")
        budget = load_budget(cfg)
        if maybe_reset_budget_period(budget):
            save_budget(cfg, budget)
        blocked = budget_check(budget)
        if blocked:
            raise RuntimeError(f"AI budget exceeded: {blocked}. Use set-ai-budget to adjust limits.")

        estimate = estimate_tokens_for_text(prompts["system"], prompts["user"], max_output_tokens=2000)
        rem = budget_remaining(budget)
        if (
            estimate["input_tokens"] > rem["input_tokens"]
            or estimate["output_tokens"] > rem["output_tokens"]
            or rem["calls"] < 1
        ):
            console.print("[yellow]AI interview evaluation may exceed remaining budget[/yellow]")

        try:
            ai_client = AIClient(
                api_key=settings["api_key"],
                model=settings["model"],
                provider=settings["provider"],
                base_url=settings["base_url"] or None,
            )
            result = ai_client.generate_text(prompts["system"], prompts["user"], max_output_tokens=2000)
            update_budget_after_call(budget, result["input_tokens"], result["output_tokens"])
            save_budget(cfg, budget)

            report_path = write_ai_report_file(cfg, args.slug, "ai_interview_eval", result["text"])
            console.print("[green]=== AI Interview Evaluation ===[/green]")
            console.print(result["text"])
            console.print(f"- report: {report_path}")
            append_log(
                cfg,
                {
                    "timestamp": datetime.now().isoformat(timespec="seconds"),
                    "action": "ai_interview_eval",
                    "slug": args.slug,
                    "provider": result["provider"],
                    "model": result["model"],
                    "input_tokens": result["input_tokens"],
                    "output_tokens": result["output_tokens"],
                    "report_path": report_path,
                },
            )
        except Exception as e:
            console.print(f"[red]AI interview evaluation failed: {e}[/red]")
        return

    if args.command == "log":
        path = append_log(
            cfg,
            {
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "pass_rate": args.pass_rate,
                "spent_min": args.spent_min,
                "cause": args.cause,
            },
        )
        console.print(tr(f"[green]日志已写入：{path}[/green]", f"[green]Log appended: {path}[/green]", ui_lang))
        return

    if args.command == "ai-feedback":
        if not args.code or not args.slug:
            raise RuntimeError("Both --code and --slug are required for ai-feedback")
        # Load user code
        code_path = Path(args.code)
        if not code_path.exists():
            raise RuntimeError(f"Code file not found: {code_path}")
        user_code = code_path.read_text(encoding="utf-8").strip()
        
        # Fetch problem detail
        cookie = os.getenv("LEETCODE_COOKIE", "").strip()
        if not cookie:
            raise RuntimeError(tr("未检测到 LEETCODE_COOKIE", "LEETCODE_COOKIE is missing", ui_lang))
        client = LeetCodeClient(cookie)
        detail = client.fetch_problem_detail(args.slug)
        
        # Prepare AI feedback prompt
        api_key = (args.api_key or os.getenv("OPENAI_API_KEY", "")).strip()
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is missing. Set env or pass --api-key")
        model = args.model or os.getenv("OPENAI_MODEL", "gpt-5.3")
        
        system_prompt = (
            "You are an algorithm interview coach. The user has written code for a problem but it contains errors. "
            "Your task is to identify the **most critical logical error** and provide a **direction for correction**, "
            "without giving the full correct code. Be concise and focus on the core misunderstanding."
        )
        user_prompt = f"""
Problem: {detail.get('translatedTitle') or detail.get('title')}
Slug: {detail.get('titleSlug')}
Difficulty: {detail.get('difficulty')}
Tags: {', '.join([t.get('slug', '') for t in (detail.get('topicTags') or []) if t.get('slug')])}

Problem statement (may contain HTML):
{detail.get('translatedContent') or detail.get('content') or ''}

User's code:
```{args.lang or 'python3'}
{user_code}
```

Provide feedback in the following format:
## 1. Critical Error
- Identify the single most important logical error (e.g., off-by-one, missing base case, incorrect algorithm choice)
- Explain why it's wrong (refer to problem constraints or examples)

## 2. Correction Direction
- Suggest **one concrete step** to fix the error (e.g., "change the loop boundary to i < n-1", "add a check for empty input")
- Do NOT write the corrected code

## 3. Common Pitfall Reminder
- Mention a related edge case that the user should test after fixing

Keep the response under 300 words. Act like an interviewer giving a hint.
"""
        # Call AI using the same infrastructure
        # Reuse OpenAIClient with custom prompt (temporary solution)
        # We'll directly call OpenAI API for now
        import requests
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": model,
            "input": [
                {
                    "role": "system",
                    "content": [{"type": "input_text", "text": system_prompt}],
                },
                {
                    "role": "user",
                    "content": [{"type": "input_text", "text": user_prompt}],
                },
            ],
        }
        try:
            resp = requests.post(
                "https://api.openai.com/v1/responses",
                headers=headers,
                json=body,
                timeout=90,
            )
            resp.raise_for_status()
            data = resp.json()
            text = data.get("output_text", "")
            if not text:
                chunks = []
                for item in data.get("output", []):
                    for c in item.get("content", []):
                        if c.get("type") == "output_text":
                            chunks.append(c.get("text", ""))
                text = "\n".join(chunks).strip()
            console.print("[green]AI Feedback:[/green]")
            console.print(text)
            # Log the feedback
            append_log(
                cfg,
                {
                    "timestamp": datetime.now().isoformat(timespec="seconds"),
                    "action": "ai_feedback",
                    "slug": args.slug,
                    "model": model,
                },
            )
        except Exception as e:
            console.print(f"[red]AI feedback failed: {e}[/red]")
        return

    if args.command == "ai-interview-eval":
        if not args.code or not args.slug:
            raise RuntimeError("Both --code and --slug are required for ai-interview-eval")
        # Load user code
        code_path = Path(args.code)
        if not code_path.exists():
            raise RuntimeError(f"Code file not found: {code_path}")
        user_code = code_path.read_text(encoding="utf-8").strip()
        
        # Fetch problem detail
        cookie = os.getenv("LEETCODE_COOKIE", "").strip()
        if not cookie:
            raise RuntimeError(tr("未检测到 LEETCODE_COOKIE", "LEETCODE_COOKIE is missing", ui_lang))
        client = LeetCodeClient(cookie)
        detail = client.fetch_problem_detail(args.slug)
        
        # 获取API配置
        api_key = (args.api_key or os.getenv("OPENAI_API_KEY", "")).strip()
        if not api_key:
            raise RuntimeError("API Key is missing. Set env or pass --api-key")
        
        model = args.model or os.getenv("OPENAI_MODEL", "gpt-5.3")
        provider = args.provider or os.getenv("AI_PROVIDER", "openai")
        base_url = args.base_url or os.getenv("AI_BASE_URL")
        
        # 根据供应商设置环境变量名称
        if provider == "openai" and not api_key:
            api_key = os.getenv("OPENAI_API_KEY", "").strip()
        elif provider == "deepseek" and not api_key:
            api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
        elif provider == "gemini" and not api_key:
            api_key = os.getenv("GEMINI_API_KEY", "").strip()
        elif provider == "claude" and not api_key:
            api_key = os.getenv("CLAUDE_API_KEY", "").strip()
        
        if not api_key:
            raise RuntimeError(f"{provider.upper()}_API_KEY is missing. Set env or pass --api-key")
        
        # 准备AI评估提示
        system_prompt = (
            "You are a senior engineer conducting a technical interview at a top tech company (like Google, Amazon, Meta, Microsoft). "
            "Evaluate the candidate's solution based on real interview rubrics used by these companies. "
            "Focus on algorithm correctness, time/space complexity, code readability, edge case handling, and code style. "
            "Provide a clear PASS/FAIL decision with justification."
        )
        user_prompt = f"""
Problem: {detail.get('translatedTitle') or detail.get('title')}
Slug: {detail.get('titleSlug')}
Difficulty: {detail.get('difficulty')}
Tags: {', '.join([t.get('slug', '') for t in (detail.get('topicTags') or []) if t.get('slug')])}

Problem statement (may contain HTML):
{detail.get('translatedContent') or detail.get('content') or ''}

User's code:
```{args.lang or 'python3'}
{user_code}
```

Evaluate this solution as if you were a real interviewer at a top tech company. Consider the following dimensions (each 1-5 points):
1. **Algorithm Correctness**: Does the code solve the problem correctly for all inputs? Are there logical errors?
2. **Time Complexity**: Is the algorithm optimal? If not, how far from optimal?
3. **Space Complexity**: Is memory usage optimal? Any unnecessary allocations?
4. **Code Readability**: Is the code clean, well-structured, and easy to understand? Are comments clear (Chinese comments acceptable)?
5. **Edge Case Handling**: Does the code handle boundary conditions (empty input, large values, etc.)?
6. **Code Style**: Naming, comments, consistency with language conventions.
7. **Problem-Solving Communication**: Can the candidate clearly explain the algorithm steps? Are multiple solutions considered and compared?

Provide your evaluation in the following structured format:

## Interview Evaluation Result

### Overall Decision
- **PASS** / **FAIL** (choose one)

### Score Summary (1-5 each)
- Algorithm Correctness: X/5
- Time Complexity: X/5  
- Space Complexity: X/5
- Code Readability: X/5
- Edge Case Handling: X/5
- Code Style: X/5

### Detailed Feedback
- **Strengths**: List 1-3 strong points of the solution.
- **Weaknesses**: List 1-3 critical issues that would concern an interviewer.
- **Improvement Suggestions**: Concrete advice to improve the solution.

### Interviewer's Notes
- Simulate real interview comments: what would you say to the candidate?
- Would you recommend hiring based on this solution? Why or why not?

Keep the response concise but thorough (around 400-500 words). Base your decision on real interview standards from top companies.
"""
        # 使用AIClient进行调用
        try:
            ai_client = AIClient(api_key=api_key, model=model, provider=provider, base_url=base_url)
            
            # 直接调用API，使用与generate_best_solution相同的逻辑但不同的提示
            if provider in ["openai", "deepseek"]:
                body = {
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 2000
                }
                endpoint = f"{ai_client.base_url}/chat/completions"
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                }
                
            elif provider == "gemini":
                body = {
                    "contents": [
                        {
                            "parts": [
                                {"text": system_prompt + "\n\n" + user_prompt}
                            ]
                        }
                    ],
                    "generationConfig": {
                        "temperature": 0.3,
                        "maxOutputTokens": 2000,
                    }
                }
                endpoint = f"{ai_client.base_url}/models/{model}:generateContent?key={api_key}"
                headers = {"Content-Type": "application/json"}
                
            elif provider == "claude":
                body = {
                    "model": model,
                    "max_tokens": 2000,
                    "temperature": 0.3,
                    "messages": [
                        {"role": "user", "content": system_prompt + "\n\n" + user_prompt}
                    ]
                }
                endpoint = f"{ai_client.base_url}/messages"
                headers = {
                    "x-api-key": api_key,
                    "anthropic-version": "2025-10-01",  # 更新为支持Claude 4系列的版本
                    "Content-Type": "application/json",
                }
                
            else:
                body = {
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 2000
                }
                endpoint = f"{ai_client.base_url}/chat/completions"
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                }

            resp = requests.post(endpoint, headers=headers, json=body, timeout=90)
            resp.raise_for_status()
            data = resp.json()

            # 解析响应
            if provider in ["openai", "deepseek"]:
                text = data["choices"][0]["message"]["content"]
            elif provider == "gemini":
                text = data["candidates"][0]["content"]["parts"][0]["text"]
            elif provider == "claude":
                text = data["content"][0]["text"]
            else:
                text = data["choices"][0]["message"]["content"]

            console.print("[green]=== AI Interview Evaluation ===[/green]")
            console.print(text)
            
            # 记录评估日志
            append_log(
                cfg,
                {
                    "timestamp": datetime.now().isoformat(timespec="seconds"),
                    "action": "ai_interview_eval",
                    "slug": args.slug,
                    "provider": provider,
                    "model": model,
                },
            )
        except Exception as e:
            console.print(f"[red]AI interview evaluation failed: {e}[/red]")
        return

    if args.command == "set-ai-budget":
        b = load_budget(cfg)
        if args.max_calls is not None:
            b["max_calls"] = args.max_calls
        if args.max_input_tokens is not None:
            b["max_input_tokens"] = args.max_input_tokens
        if args.max_output_tokens is not None:
            b["max_output_tokens"] = args.max_output_tokens
        if args.reset_period is not None:
            period = args.reset_period.strip().lower()
            if period not in {"daily", "monthly"}:
                raise ValueError("--reset-period must be daily or monthly")
            b["reset_period"] = period
            b["period_start"] = _period_start(period, datetime.now())
            b["used_calls"] = 0
            b["used_input_tokens"] = 0
            b["used_output_tokens"] = 0
        save_budget(cfg, b)
        console.print(tr("[green]AI预算已更新[/green]", "[green]AI budget updated[/green]", ui_lang))
        print_budget_summary(b, ui_lang)
        return

    if args.command == "show-ai-budget":
        b = load_budget(cfg)
        if maybe_reset_budget_period(b):
            save_budget(cfg, b)
        print_budget_summary(b, ui_lang)
        return

    cookie = os.getenv("LEETCODE_COOKIE", "").strip()
    if not cookie:
        raise RuntimeError(tr("未检测到 LEETCODE_COOKIE", "LEETCODE_COOKIE is missing", ui_lang))

    client = LeetCodeClient(cookie)

    if args.command == "check-auth":
        status = client.check_auth()
        is_signed_in = bool(status.get("isSignedIn"))
        if is_signed_in:
            console.print(
                tr(
                    f"[green]Cookie 有效，当前已登录：{status.get('username', '')}[/green]",
                    f"[green]Cookie is valid. Signed in as: {status.get('username', '')}[/green]",
                    ui_lang,
                )
            )
        else:
            console.print(tr("[yellow]Cookie 无效[/yellow]", "[yellow]Cookie may be invalid[/yellow]", ui_lang))
        return

    default_limit = int(os.getenv("DEFAULT_LIMIT", str(cfg["filters"].get("limit", 10))))
    limit = args.limit or default_limit
    problems = client.fetch_problemset(limit=limit, skip=0)
    unsolved = filter_unsolved(problems)
    d = [x.strip().upper() for x in args.difficulty.split(",") if x.strip()] if args.difficulty else None
    tg = [x.strip().lower() for x in args.tags.split(",") if x.strip()] if args.tags else None
    filtered = apply_filters(unsolved, d, tg)

    if not filtered:
        console.print(tr("[yellow]未找到符合条件题目[/yellow]", "[yellow]No matching unsolved problem[/yellow]", ui_lang))
        return

    if args.command == "list":
        print_problem_table(filtered, ui_lang)
        return

    lang = args.lang or os.getenv("DEFAULT_LANG", "python3")

    if args.command == "recommend":
        chosen = recommend_problem(filtered)
        paths = write_simple_files(cfg, chosen, lang)
        console.print(f"Recommended: {chosen.frontend_id} {chosen.title}")
        for k, v in paths.items():
            console.print(f"- {k}: {v}")
        maybe_open_problem(args, chosen, ui_lang)
        append_log(cfg, {"timestamp": datetime.now().isoformat(timespec="seconds"), "action": "recommend", "slug": chosen.title_slug})
        return

    print_problem_table(filtered, ui_lang)
    chosen = choose_problem(filtered, args.pick, ui_lang)

    if args.command == "prepare":
        paths = write_simple_files(cfg, chosen, lang)
        console.print(tr("[green]已生成学习文件[/green]", "[green]Study files generated[/green]", ui_lang))
        for k, v in paths.items():
            console.print(f"- {k}: {v}")
        maybe_open_problem(args, chosen, ui_lang)
        append_log(cfg, {"timestamp": datetime.now().isoformat(timespec="seconds"), "action": "prepare", "slug": chosen.title_slug})
        return

    if args.command == "fallback-solve":
        if not args.force:
            ans = console.input(tr("生成兜底学习模板？(y/N): ", "Generate fallback study template? (y/N): ", ui_lang)).strip().lower()
            if ans not in {"y", "yes"}:
                return
        paths = write_simple_files(cfg, chosen, lang, prefix="fallback_")
        for k, v in paths.items():
            console.print(f"- {k}: {v}")
        append_log(cfg, {"timestamp": datetime.now().isoformat(timespec="seconds"), "action": "fallback_solve", "slug": chosen.title_slug})
        return

    if args.command == "estimate-ai-fallback":
        budget = load_budget(cfg)
        if maybe_reset_budget_period(budget):
            save_budget(cfg, budget)
        detail = client.fetch_problem_detail(chosen.title_slug)
        est = estimate_tokens_for_prompt(detail, compare=args.compare)
        rem = budget_remaining(budget)
        print_budget_summary(budget, ui_lang)
        console.print(
            tr(
                f"[cyan]预估本次消耗: input≈{est['input_tokens']} output≈{est['output_tokens']}[/cyan]",
                f"[cyan]Estimated this call: input≈{est['input_tokens']} output≈{est['output_tokens']}[/cyan]",
                ui_lang,
            )
        )
        console.print(
            tr(
                f"[cyan]调用后预计剩余: calls={max(0, rem['calls']-1)} input={max(0, rem['input_tokens']-est['input_tokens'])} output={max(0, rem['output_tokens']-est['output_tokens'])}[/cyan]",
                f"[cyan]Estimated remaining after call: calls={max(0, rem['calls']-1)} input={max(0, rem['input_tokens']-est['input_tokens'])} output={max(0, rem['output_tokens']-est['output_tokens'])}[/cyan]",
                ui_lang,
            )
        )
        return

    if args.command == "ai-fallback":
        budget = load_budget(cfg)
        if maybe_reset_budget_period(budget):
            save_budget(cfg, budget)

        blocked = budget_check(budget)
        if blocked:
            raise RuntimeError(f"AI budget exceeded: {blocked}. Use set-ai-budget to adjust limits.")

        print_budget_summary(budget, ui_lang)

        if not args.force:
            ans = console.input(
                tr(
                    "将调用大模型生成参考最优解（消耗token），确认继续？(y/N): ",
                    "This will call model API and consume tokens. Continue? (y/N): ",
                    ui_lang,
                )
            ).strip().lower()
            if ans not in {"y", "yes"}:
                return

        # 获取API配置
        api_key = (args.api_key or os.getenv("OPENAI_API_KEY", "")).strip()
        if not api_key:
            raise RuntimeError("API Key is missing. Set env or pass --api-key")
        
        model = args.model or os.getenv("OPENAI_MODEL", "gpt-5.3")
        provider = args.provider or os.getenv("AI_PROVIDER", "openai")
        base_url = args.base_url or os.getenv("AI_BASE_URL")
        
        # 根据供应商设置环境变量名称
        if provider == "openai" and not api_key:
            api_key = os.getenv("OPENAI_API_KEY", "").strip()
        elif provider == "deepseek" and not api_key:
            api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
        elif provider == "gemini" and not api_key:
            api_key = os.getenv("GEMINI_API_KEY", "").strip()
        elif provider == "claude" and not api_key:
            api_key = os.getenv("CLAUDE_API_KEY", "").strip()
        
        if not api_key:
            raise RuntimeError(f"{provider.upper()}_API_KEY is missing. Set env or pass --api-key")

        detail = client.fetch_problem_detail(chosen.title_slug)

        if not args.no_estimate:
            est = estimate_tokens_for_prompt(detail, compare=args.compare)
            rem = budget_remaining(budget)
            console.print(
                tr(
                    f"[cyan]预估本次消耗: input≈{est['input_tokens']} output≈{est['output_tokens']}[/cyan]",
                    f"[cyan]Estimated this call: input≈{est['input_tokens']} output≈{est['output_tokens']}[/cyan]",
                    ui_lang,
                )
            )
            if est["input_tokens"] > rem["input_tokens"] or est["output_tokens"] > rem["output_tokens"] or rem["calls"] < 1:
                console.print(
                    tr(
                        "[yellow]警告：按预估可能超预算。[/yellow]",
                        "[yellow]Warning: estimate may exceed remaining budget.[/yellow]",
                        ui_lang,
                    )
                )
            if not args.force:
                c2 = console.input(
                    tr(
                        "是否按该预估继续调用？(y/N): ",
                        "Proceed with this estimate? (y/N): ",
                        ui_lang,
                    )
                ).strip().lower()
                if c2 not in {"y", "yes"}:
                    return

        ai_client = AIClient(api_key=api_key, model=model, provider=provider, base_url=base_url)
        result = ai_client.generate_best_solution(detail, lang=lang, compare=args.compare)

        update_budget_after_call(budget, result["input_tokens"], result["output_tokens"])
        save_budget(cfg, budget)

        paths = write_ai_solution_files(cfg, chosen, result["text"])
        console.print(tr("[green]AI参考解已生成[/green]", "[green]AI reference solution generated[/green]", ui_lang))
        for k, v in paths.items():
            console.print(f"- {k}: {v}")
        console.print(
            f"provider={result.get('provider', 'openai')} model={result['model']} input_tokens={result['input_tokens']} output_tokens={result['output_tokens']} calls={budget['used_calls']}/{budget['max_calls']}"
        )
        print_budget_summary(budget, ui_lang)
        append_log(
            cfg,
            {
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "action": "ai_fallback",
                "slug": chosen.title_slug,
                "provider": result.get("provider", "openai"),
                "model": result["model"],
                "input_tokens": result["input_tokens"],
                "output_tokens": result["output_tokens"],
            },
        )
        maybe_open_problem(args, chosen, ui_lang)
        return


if __name__ == "__main__":
    main()
