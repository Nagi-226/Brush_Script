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


st.set_page_config(page_title="Brush Script - 智能刷题助手", layout="wide")

# 初始化session状态
if "estimate_ready" not in st.session_state:
    st.session_state.estimate_ready = False
if "last_params" not in st.session_state:
    st.session_state.last_params = {}
if "current_mode" not in st.session_state:
    st.session_state.current_mode = "ai_fallback"  # 默认模式：AI参考解生成

# ==================== 侧边栏配置 ====================
with st.sidebar:
    st.markdown("## 🎯 " + t("工作模式", "Work Mode", "cn"))
    
    # 模式选择器
    mode_options = {
        "ai_fallback": t("AI参考解生成", "AI Solution Generator", "cn"),
        "interview_eval": t("模拟面试评估", "Mock Interview Evaluation", "cn"),
        "practice_mode": t("刷题训练", "Practice Mode", "cn")  # 预留
    }
    
    current_mode = st.radio(
        t("选择工作模式", "Select Work Mode", "cn"),
        options=list(mode_options.keys()),
        format_func=lambda x: mode_options[x],
        index=0
    )
    
    # 更新session状态
    if current_mode != st.session_state.current_mode:
        st.session_state.current_mode = current_mode
        st.rerun()
    
    st.markdown("---")
    
    # 语言选择
    st.markdown("## 🌐 " + t("界面语言", "UI Language", "cn"))
    ui_lang = st.selectbox(t("选择语言", "Select Language", "cn"), ["en", "cn"], index=0, label_visibility="collapsed")
    
    st.markdown("---")
    
    # API配置（所有模式共用）
    st.markdown("## 🔑 " + t("AI模型配置", "AI Model Configuration", "cn"))
    
    # 模型供应商选择
    provider_options = {
        "openai": t("OpenAI", "OpenAI", ui_lang),
        "deepseek": t("DeepSeek", "DeepSeek", ui_lang),
        "gemini": t("Google Gemini", "Google Gemini", ui_lang),
        "claude": t("Anthropic Claude", "Anthropic Claude", ui_lang),
        "custom": t("自定义API", "Custom API", ui_lang)
    }
    
    provider = st.selectbox(
        t("选择AI供应商", "Select AI Provider", ui_lang),
        options=list(provider_options.keys()),
        format_func=lambda x: provider_options[x],
        index=0
    )
    
    # 根据供应商显示不同的配置
    if provider == "openai":
        api_key = st.text_input(
            t("OpenAI API Key", "OpenAI API Key", ui_lang), 
            type="password", 
            placeholder="sk-...",
            help=t("从 platform.openai.com 获取", "Get from platform.openai.com", ui_lang)
        )
        model = st.selectbox(
            t("OpenAI模型", "OpenAI Model", ui_lang),
            ["gpt-5.3", "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"],
            index=0
        )
        base_url = "https://api.openai.com/v1"
        
    elif provider == "deepseek":
        api_key = st.text_input(
            t("DeepSeek API Key", "DeepSeek API Key", ui_lang),
            type="password",
            placeholder="sk-...",
            help=t("从 platform.deepseek.com 获取", "Get from platform.deepseek.com", ui_lang)
        )
        model = st.selectbox(
            t("DeepSeek模型", "DeepSeek Model", ui_lang),
            ["deepseek-chat", "deepseek-coder", "deepseek-v3.2"],
            index=2
        )
        base_url = "https://api.deepseek.com/v1"
        
    elif provider == "gemini":
        api_key = st.text_input(
            t("Google API Key", "Google API Key", ui_lang),
            type="password",
            placeholder="AIza...",
            help=t("从 makersuite.google.com 获取", "Get from makersuite.google.com", ui_lang)
        )
        model = st.selectbox(
            t("Gemini模型", "Gemini Model", ui_lang),
            [
                "gemini-3.0-pro",  # Gemini 3.0 Pro (最新旗舰)
                "gemini-3.0-flash",  # Gemini 3.0 Flash (快速版)
                "gemini-2.0-flash",  # Gemini 2.0 Flash (上一代快速版)
                "gemini-2.0-pro",  # Gemini 2.0 Pro (上一代专业版)
                "gemini-1.5-pro",  # Gemini 1.5 Pro (长上下文版)
                "gemini-1.5-flash"  # Gemini 1.5 Flash (快速长上下文版)
            ],
            index=0
        )
        base_url = "https://generativelanguage.googleapis.com/v1beta"
        
    elif provider == "claude":
        api_key = st.text_input(
            t("Anthropic API Key", "Anthropic API Key", ui_lang),
            type="password",
            placeholder="sk-ant-...",
            help=t("从 console.anthropic.com 获取", "Get from console.anthropic.com", ui_lang)
        )
        model = st.selectbox(
            t("Claude模型", "Claude Model", ui_lang),
            [
                "claude-4-opus",  # Claude 4 Opus (最新旗舰)
                "claude-4-sonnet",  # Claude 4 Sonnet (平衡版)
                "claude-4-haiku",  # Claude 4 Haiku (快速版)
                "claude-3-5-sonnet",  # Claude 3.5 Sonnet (上一代旗舰)
                "claude-3-opus",  # Claude 3 Opus (上一代专业版)
                "claude-3-haiku"  # Claude 3 Haiku (上一代快速版)
            ],
            index=0
        )
        base_url = "https://api.anthropic.com/v1"
        
    else:  # custom
        api_key = st.text_input(
            t("API Key", "API Key", ui_lang),
            type="password",
            placeholder="输入API密钥",
            help=t("自定义API的密钥", "API key for custom provider", ui_lang)
        )
        model = st.text_input(
            t("模型名称", "Model Name", ui_lang),
            value="custom-model",
            help=t("自定义模型名称", "Custom model name", ui_lang)
        )
        base_url = st.text_input(
            t("API基础地址", "API Base URL", ui_lang),
            value="https://api.example.com/v1",
            help=t("自定义API的基础地址", "Base URL for custom API", ui_lang)
        )
    
    # 保存供应商配置到session状态
    if "ai_provider" not in st.session_state:
        st.session_state.ai_provider = provider
    if "ai_base_url" not in st.session_state:
        st.session_state.ai_base_url = base_url
    
    # 更新session状态
    if provider != st.session_state.ai_provider:
        st.session_state.ai_provider = provider
        st.session_state.ai_base_url = base_url
    
    # 根据模式显示不同的语言选择
    if st.session_state.current_mode == "ai_fallback":
        lang = st.selectbox(t("代码语言", "Code Language", ui_lang), ["python3", "cpp", "java"], index=0)
    elif st.session_state.current_mode == "interview_eval":
        eval_lang = st.selectbox(t("代码语言", "Code Language", ui_lang), ["python3", "cpp", "java"], index=0)
    
    st.markdown("---")
    
    # 预算管理（所有模式共用）
    st.markdown("## 💰 " + t("预算管理", "Budget Management", "cn"))
    max_calls = st.number_input(t("最大调用次数", "Max Calls", ui_lang), min_value=1, value=20, step=1)
    max_in = st.number_input(t("最大输入 Tokens", "Max Input Tokens", ui_lang), min_value=1000, value=200000, step=1000)
    max_out = st.number_input(t("最大输出 Tokens", "Max Output Tokens", ui_lang), min_value=1000, value=200000, step=1000)
    reset_period = st.selectbox(t("重置周期", "Reset Period", ui_lang), ["daily", "monthly"], index=0)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button(t("保存预算", "Save Budget", ui_lang), use_container_width=True):
            cmd = [
                "python", "main.py", "set-ai-budget",
                "--max-calls", str(max_calls),
                "--max-input-tokens", str(max_in),
                "--max-output-tokens", str(max_out),
                "--reset-period", reset_period,
                "--ui-lang", ui_lang,
            ]
            st.code(run_cmd(cmd))
    
    with col2:
        if st.button(t("刷新额度", "Refresh Budget", ui_lang), use_container_width=True):
            st.code(run_cmd(["python", "main.py", "show-ai-budget", "--ui-lang", ui_lang]))

# ==================== 主标题 ====================
st.title(f"Brush Script - {mode_options[st.session_state.current_mode]}")
st.caption(t(
    "智能刷题助手，提升算法学习效率",
    "Intelligent coding assistant for efficient algorithm learning",
    ui_lang
))

# ==================== 当前预算状态 ====================
with st.expander(t("📊 当前预算状态", "📊 Current Budget Status", ui_lang), expanded=True):
    st.code(run_cmd(["python", "main.py", "show-ai-budget", "--ui-lang", ui_lang]))

# ==================== 模式路由 ====================
def render_ai_fallback_mode(ui_lang, api_key, model, lang, provider, base_url):
    """渲染AI参考解生成模式"""
    st.markdown("## 🚀 " + t("AI参考解生成", "AI Solution Generator", ui_lang))
    st.caption(t(
        "选择题目筛选条件，一键生成AI参考最优解（最小时间复杂度优先）",
        "Select problem filters and generate AI reference solution (minimum time complexity first)",
        ui_lang
    ))
    
    with st.expander(t("📋 题目筛选条件", "📋 Problem Filters", ui_lang), expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            difficulty = st.text_input(t("难度", "Difficulty", ui_lang), value="EASY,MEDIUM", 
                                      help=t("如: EASY,MEDIUM,HARD", "e.g., EASY,MEDIUM,HARD", ui_lang))
            limit = st.number_input(t("拉取数量", "Fetch Limit", ui_lang), min_value=1, max_value=200, value=30, step=1)
        with col2:
            tags = st.text_input(t("标签", "Tags", ui_lang), value="", 
                                help=t("如: array,hash-table", "e.g., array,hash-table", ui_lang))
            pick = st.number_input(t("选择序号", "Pick Row #", ui_lang), min_value=1, value=1, step=1)
    
    require_estimate = st.checkbox(t("调用前必须先做 Token 预估", "Require token estimate before AI call", ui_lang), value=True)
    
    # 两步流程
    st.markdown("### " + t("📈 步骤 1：Token预估", "📈 Step 1: Token Estimation", ui_lang))
    if st.button(t("预估本次调用 Tokens", "Estimate Tokens for This Run", ui_lang), use_container_width=True):
        est_cmd = [
            "python", "main.py", "estimate-ai-fallback",
            "--difficulty", difficulty.strip(),
            "--tags", tags.strip(),
            "--limit", str(limit),
            "--pick", str(pick),
            "--ui-lang", ui_lang,
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
    
    st.markdown("### " + t("⚡ 步骤 2：生成参考解", "⚡ Step 2: Generate Solution", ui_lang))
    if require_estimate and not st.session_state.estimate_ready:
        st.info(t("请先执行 Token 预估。", "Please run token estimate first.", ui_lang))
    
    if st.button(t("🚀 一键生成 AI 参考最优解", "🚀 One-click Generate AI Best Solution", ui_lang), 
                 type="primary", use_container_width=True):
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
                        "python", "main.py", "ai-fallback",
                        "--api-key", api_key.strip(),
                        "--model", model.strip(),
                        "--provider", provider,
                        "--base-url", base_url,
                        "--lang", lang,
                        "--difficulty", difficulty.strip(),
                        "--tags", tags.strip(),
                        "--limit", str(limit),
                        "--pick", str(pick),
                        "--force",
                        "--ui-lang", ui_lang,
                    ]
                    if require_estimate:
                        cmd.append("--no-estimate")
                    
                    with st.spinner(t("AI正在生成参考解...", "AI is generating reference solution...", ui_lang)):
                        output = run_cmd(cmd)
                        if "Traceback" in output or "RuntimeError" in output:
                            st.error(t("生成失败。", "Generation failed.", ui_lang))
                            st.code(output)
                        else:
                            st.success(t("✅ 生成成功！", "✅ Generated successfully!", ui_lang))
                            with st.expander(t("查看生成结果", "View Generated Result", ui_lang), expanded=True):
                                st.code(output)
                            st.session_state.estimate_ready = False

def render_interview_eval_mode(ui_lang, api_key, model, eval_lang, provider, base_url):
    """渲染模拟面试评估模式"""
    st.markdown("## 👨‍💼 " + t("模拟大厂技术面试评估", "Mock Big Tech Interview Evaluation", ui_lang))
    st.caption(t(
        "上传你的代码，获取模拟真实大厂技术面试的通过/不通过判定与详细反馈",
        "Upload your code to get PASS/FAIL decision with detailed feedback simulating real tech company interviews",
        ui_lang
    ))
    
    # 评估说明
    with st.expander(t("📝 评估说明", "📝 Evaluation Notes", ui_lang), expanded=False):
        st.markdown(t("""
        ### 🎯 评估标准
        - 基于 Google、Amazon、Meta、Microsoft 等公司的真实面试评分卡
        - 特别针对国内大厂（腾讯、字节跳动、阿里巴巴、华为）面试环境优化
        
        ### 📊 考核维度
        1. **算法正确性** - 解决方案是否正确
        2. **时间复杂度** - 算法效率分析
        3. **空间复杂度** - 内存使用优化
        4. **代码可读性** - 支持中文注释评估
        5. **边界情况处理** - 特殊输入处理能力
        6. **代码风格** - 命名规范、结构清晰度
        7. **解题思路沟通** - 解释算法的能力
        
        ### 📋 输出格式
        - 明确的 PASS/FAIL 决定
        - 结构化评分（1-5分每个维度）
        - 优缺点分析
        - 具体改进建议
        - 面试官模拟评论
        """, """
        ### 🎯 Evaluation Criteria
        - Based on real interview rubrics from Google, Amazon, Meta, Microsoft, etc.
        - Optimized for domestic big tech companies (Tencent, ByteDance, Alibaba, Huawei)
        
        ### 📊 Assessment Dimensions
        1. **Algorithm Correctness** - Solution accuracy
        2. **Time Complexity** - Algorithm efficiency analysis
        3. **Space Complexity** - Memory usage optimization
        4. **Code Readability** - Supports Chinese comments evaluation
        5. **Edge Case Handling** - Special input processing capability
        6. **Code Style** - Naming conventions, structure clarity
        7. **Problem-Solving Communication** - Ability to explain algorithms
        
        ### 📋 Output Format
        - Clear PASS/FAIL decision
        - Structured scoring (1-5 points per dimension)
        - Strengths and weaknesses analysis
        - Specific improvement suggestions
        - Interviewer simulation comments
        """, ui_lang))
    
    # 输入表单
    st.markdown("### " + t("📥 输入你的代码", "📥 Input Your Code", ui_lang))
    
    col1, col2 = st.columns([1, 2])
    with col1:
        eval_slug = st.text_input(
            t("题目 Slug", "Problem Slug", ui_lang), 
            placeholder="two-sum", 
            help=t("题目的唯一标识，如 two-sum", "Problem unique identifier, e.g., two-sum", ui_lang)
        )
        eval_lang_display = st.selectbox(
            t("代码语言", "Code Language", ui_lang), 
            ["python3", "cpp", "java"], 
            index=0
        )
    
    with col2:
        default_code = t("""def two_sum(nums, target):
    \"\"\"
    两数之和解决方案
    参数:
        nums: 整数列表
        target: 目标值
    返回:
        两个数的索引列表
    \"\"\"
    # 在这里编写你的代码
    pass""", 
    """def two_sum(nums, target):
    \"\"\"
    Two Sum solution
    Args:
        nums: List of integers
        target: Target value
    Returns:
        List of two indices
    \"\"\"
    # Write your code here
    pass""", ui_lang)
        
        eval_code = st.text_area(
            t("你的代码", "Your Code", ui_lang), 
            height=250, 
            value=default_code,
            placeholder=t("def solve(...):\n    # 你的代码...", "def solve(...):\n    # Your code...", ui_lang), 
            help=t("粘贴你的完整解决方案代码", "Paste your complete solution code", ui_lang)
        )
    
    # 评估按钮
    if st.button(t("🎯 运行面试评估", "🎯 Run Interview Evaluation", ui_lang), 
                 type="primary", use_container_width=True):
        if not eval_slug.strip():
            st.error(t("请输入题目 Slug", "Please enter problem slug", ui_lang))
        elif not eval_code.strip():
            st.error(t("请输入你的代码", "Please enter your code", ui_lang))
        elif not api_key.strip():
            st.error(t("请先输入 API Key", "Please enter API Key first", ui_lang))
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
                    "python", "main.py", "ai-interview-eval",
                    "--code", tmp_path,
                    "--slug", eval_slug.strip(),
                    "--lang", eval_lang_display,
                    "--api-key", api_key.strip(),
                    "--model", model.strip(),
                    "--provider", provider,
                    "--base-url", base_url,
                ]
                
                with st.spinner(t("🤔 AI面试官正在评估中...", "🤔 AI interviewer is evaluating...", ui_lang)):
                    output = run_cmd(cmd)
                    if "Traceback" in output or "RuntimeError" in output:
                        st.error(t("❌ 评估失败", "❌ Evaluation failed", ui_lang))
                        with st.expander(t("查看错误详情", "View Error Details", ui_lang)):
                            st.code(output)
                    else:
                        st.success(t("✅ 评估完成！", "✅ Evaluation completed!", ui_lang))
                        with st.expander(t("📋 查看评估报告", "📋 View Evaluation Report", ui_lang), expanded=True):
                            st.markdown(output)
            finally:
                os.unlink(tmp_path)

def render_practice_mode(ui_lang):
    """渲染刷题训练模式（预留）"""
    st.markdown("## 📚 " + t("刷题训练模式", "Practice Mode", ui_lang))
    st.info(t("此功能正在开发中，敬请期待！", "This feature is under development, stay tuned!", ui_lang))
    st.caption(t(
        "规划功能：个性化训练计划、进度跟踪、弱点分析",
        "Planned features: Personalized training plans, progress tracking, weakness analysis",
        ui_lang
    ))

# ==================== 根据模式渲染内容 ====================
if st.session_state.current_mode == "ai_fallback":
    render_ai_fallback_mode(ui_lang, api_key, model, lang, st.session_state.ai_provider, st.session_state.ai_base_url)
elif st.session_state.current_mode == "interview_eval":
    render_interview_eval_mode(ui_lang, api_key, model, eval_lang, st.session_state.ai_provider, st.session_state.ai_base_url)
elif st.session_state.current_mode == "practice_mode":
    render_practice_mode(ui_lang)

# ==================== 页脚 ====================
st.markdown("---")
st.caption(t(
    "💡 提示：启动方式 `streamlit run app.py` | 项目文档请查看 README.md",
    "💡 Tip: Start with `streamlit run app.py` | See README.md for project documentation",
    ui_lang
))
