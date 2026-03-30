import os
import subprocess
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).parent


def t(cn: str, en: str, ui_lang: str) -> str:
    return cn if ui_lang == "cn" else en


def run_cmd(cmd: list[str]) -> str:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["NO_COLOR"] = "1"
    out = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, env=env)
    return (out.stdout or "") + (out.stderr or "")


st.set_page_config(page_title="Brush Script AI Fallback", layout="wide")

if "estimate_ready" not in st.session_state:
    st.session_state.estimate_ready = False
if "last_params" not in st.session_state:
    st.session_state.last_params = {}

# Sidebar language first
with st.sidebar:
    ui_lang = st.selectbox("UI Language", ["en", "cn"], index=0)

st.title(t("Brush Script - 一键 AI 最优解兜底", "Brush Script - One Click AI Best-Solution Fallback", ui_lang))
st.caption(
    t(
        "选择题目筛选条件，输入 API Key，点击按钮生成 AI 参考最优解（最小时间复杂度优先）。",
        "Pick filters, input API Key, then generate AI fallback solution (min time complexity first).",
        ui_lang,
    )
)

with st.sidebar:
    st.header(t("API / 模型", "API / Model", ui_lang))
    api_key = st.text_input(t("OpenAI API Key", "OpenAI API Key", ui_lang), type="password", placeholder="sk-...")
    model = st.text_input(t("模型", "Model", ui_lang), value="gpt-5.3")
    lang = st.selectbox(t("代码语言", "Code Language", ui_lang), ["python3", "cpp", "java"], index=0)

st.subheader(t("预算上限（防超支）", "Budget Limits (anti-overspending)", ui_lang))
col1, col2, col3, col4 = st.columns(4)
with col1:
    max_calls = st.number_input(t("最大调用次数", "Max Calls", ui_lang), min_value=1, value=20, step=1)
with col2:
    max_in = st.number_input(t("最大输入 Tokens", "Max Input Tokens", ui_lang), min_value=1000, value=200000, step=1000)
with col3:
    max_out = st.number_input(t("最大输出 Tokens", "Max Output Tokens", ui_lang), min_value=1000, value=200000, step=1000)
with col4:
    reset_period = st.selectbox(t("重置周期", "Reset Period", ui_lang), ["daily", "monthly"], index=0)

save_budget_col, refresh_budget_col = st.columns([1, 1])
with save_budget_col:
    if st.button(t("保存预算配置", "Save Budget Limits", ui_lang)):
        cmd = [
            "python",
            "main.py",
            "set-ai-budget",
            "--max-calls",
            str(max_calls),
            "--max-input-tokens",
            str(max_in),
            "--max-output-tokens",
            str(max_out),
            "--reset-period",
            reset_period,
            "--ui-lang",
            ui_lang,
        ]
        st.code(run_cmd(cmd))

with refresh_budget_col:
    if st.button(t("刷新剩余额度", "Refresh Remaining Budget", ui_lang)):
        st.code(run_cmd(["python", "main.py", "show-ai-budget", "--ui-lang", ui_lang]))

st.caption(t("当前预算快照", "Current budget snapshot", ui_lang))
st.code(run_cmd(["python", "main.py", "show-ai-budget", "--ui-lang", ui_lang]))

st.subheader(t("题目筛选", "Problem Filters", ui_lang))
difficulty = st.text_input(t("难度", "Difficulty", ui_lang), value="EASY,MEDIUM")
tags = st.text_input(t("标签", "Tags", ui_lang), value="")
limit = st.number_input(t("拉取数量", "Fetch Limit", ui_lang), min_value=1, max_value=200, value=30, step=1)
pick = st.number_input(t("选择序号", "Pick Row #", ui_lang), min_value=1, value=1, step=1)

require_estimate = st.checkbox(t("调用前必须先做 Token 预估", "Require token estimate before AI call", ui_lang), value=True)

st.markdown(f"### {t('步骤 1：预估', 'Step 1: Estimate', ui_lang)}")
if st.button(t("预估本次调用 Tokens", "Estimate Tokens for This Run", ui_lang)):
    est_cmd = [
        "python",
        "main.py",
        "estimate-ai-fallback",
        "--difficulty",
        difficulty.strip(),
        "--tags",
        tags.strip(),
        "--limit",
        str(limit),
        "--pick",
        str(pick),
        "--ui-lang",
        ui_lang,
    ]
    st.code(run_cmd(est_cmd))
    st.session_state.estimate_ready = True
    st.session_state.last_params = {
        "difficulty": difficulty.strip(),
        "tags": tags.strip(),
        "limit": int(limit),
        "pick": int(pick),
        "ui_lang": ui_lang,
    }

st.markdown(f"### {t('步骤 2：生成', 'Step 2: Generate', ui_lang)}")
if require_estimate and not st.session_state.estimate_ready:
    st.info(t("请先执行 Token 预估。", "Please run token estimate first.", ui_lang))

if st.button(t("一键生成 AI 参考最优解", "One-click Generate AI Best Solution", ui_lang), type="primary"):
    if not api_key.strip():
        st.error(t("请先输入 API Key。", "Please input API Key first.", ui_lang))
    else:
        if require_estimate and not st.session_state.estimate_ready:
            st.error(t("生成前必须先预估。", "Token estimate is required before generation.", ui_lang))
        else:
            current_params = {
                "difficulty": difficulty.strip(),
                "tags": tags.strip(),
                "limit": int(limit),
                "pick": int(pick),
                "ui_lang": ui_lang,
            }
            if require_estimate and current_params != st.session_state.last_params:
                st.error(t("你在预估后修改了筛选条件，请重新预估。", "Filters changed after estimate. Please estimate again.", ui_lang))
            else:
                cmd = [
                    "python",
                    "main.py",
                    "ai-fallback",
                    "--api-key",
                    api_key.strip(),
                    "--model",
                    model.strip(),
                    "--lang",
                    lang,
                    "--difficulty",
                    difficulty.strip(),
                    "--tags",
                    tags.strip(),
                    "--limit",
                    str(limit),
                    "--pick",
                    str(pick),
                    "--force",
                    "--ui-lang",
                    ui_lang,
                ]
                if require_estimate:
                    cmd.append("--no-estimate")

                output = run_cmd(cmd)
                if "Traceback" in output or "RuntimeError" in output:
                    st.error(t("生成失败。", "Generation failed.", ui_lang))
                    st.code(output)
                else:
                    st.success(t("生成成功。", "Generated successfully.", ui_lang))
                    st.code(output)
                    st.session_state.estimate_ready = False

st.markdown("---")
st.subheader(t("模拟大厂技术面试评估", "Mock Big Tech Interview Evaluation", ui_lang))
st.caption(t(
    "上传你的代码，获取模拟真实大厂技术面试的通过/不通过判定与详细反馈。",
    "Upload your code to get a PASS/FAIL decision with detailed feedback simulating real tech company interviews.",
    ui_lang
))

with st.expander(t("评估说明", "Evaluation Notes", ui_lang), expanded=False):
    st.markdown(t("""
    - **评估标准**：基于 Google、Amazon、Meta、Microsoft 等公司的真实面试评分卡
    - **考核维度**：算法正确性、时间复杂度、空间复杂度、代码可读性、边界情况处理、代码风格
    - **判定结果**：明确给出 PASS（通过）或 FAIL（不通过）决定，并附有详细理由
    - **反馈格式**：结构化评分 + 优缺点分析 + 改进建议 + 面试官模拟评论
    """, """
    - **Evaluation Criteria**: Based on real interview rubrics from Google, Amazon, Meta, Microsoft, etc.
    - **Dimensions**: Algorithm correctness, time complexity, space complexity, code readability, edge case handling, code style
    - **Decision**: Clear PASS or FAIL decision with detailed justification
    - **Feedback Format**: Structured scores + strengths/weaknesses + improvement suggestions + interviewer comments
    """, ui_lang))

col1, col2 = st.columns(2)
with col1:
    eval_slug = st.text_input(t("题目 Slug", "Problem Slug", ui_lang), placeholder="two-sum", help="题目的唯一标识，如 two-sum")
    eval_lang = st.selectbox(t("代码语言", "Code Language", ui_lang), ["python3", "cpp", "java"], index=0)
with col2:
    eval_code = st.text_area(t("你的代码", "Your Code", ui_lang), height=200, 
                             placeholder="def solve(...):\n    # 你的代码...", 
                             help="粘贴你的完整解决方案代码")

if st.button(t("运行面试评估", "Run Interview Evaluation", ui_lang), type="secondary"):
    if not eval_slug.strip():
        st.error(t("请输入题目 Slug", "Please enter problem slug", ui_lang))
    elif not eval_code.strip():
        st.error(t("请输入你的代码", "Please enter your code", ui_lang))
    else:
        # 创建临时文件保存代码
        import tempfile
        import os
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
            f.write(eval_code)
            tmp_path = f.name
        
        try:
            # 构建命令
            cmd = [
                "python",
                "main.py",
                "ai-interview-eval",
                "--code",
                tmp_path,
                "--slug",
                eval_slug.strip(),
                "--lang",
                eval_lang,
            ]
            # 使用侧边栏的 API 配置
            if api_key.strip():
                cmd.extend(["--api-key", api_key.strip()])
            if model.strip():
                cmd.extend(["--model", model.strip()])
            
            with st.spinner(t("AI 面试官评估中...", "AI interviewer evaluating...", ui_lang)):
                output = run_cmd(cmd)
                if "Traceback" in output or "RuntimeError" in output:
                    st.error(t("评估失败", "Evaluation failed", ui_lang))
                    st.code(output)
                else:
                    st.success(t("评估完成", "Evaluation completed", ui_lang))
                    st.markdown(output)
        finally:
            os.unlink(tmp_path)

st.markdown("---")
st.caption(t("启动方式：streamlit run app.py", "Start web UI with: streamlit run app.py", ui_lang))
