import subprocess
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).parent

st.set_page_config(page_title="Brush Script AI Fallback", layout="wide")
st.title("Brush Script - One Click AI Best-Solution Fallback")
st.caption("选择题目筛选条件，输入 API Key，点击按钮生成 AI 参考最优解（最小时间复杂度优先）。")

if "estimate_ready" not in st.session_state:
    st.session_state.estimate_ready = False
if "last_params" not in st.session_state:
    st.session_state.last_params = {}

with st.sidebar:
    st.header("API / Model")
    api_key = st.text_input("OpenAI API Key", type="password", placeholder="sk-...")
    model = st.text_input("Model", value="gpt-5.3")
    lang = st.selectbox("Code Language", ["python3", "cpp", "java"], index=0)
    ui_lang = st.selectbox("UI Language", ["en", "zh"], index=0)

st.subheader("Budget Limits (anti-overspending)")
col1, col2, col3, col4 = st.columns(4)
with col1:
    max_calls = st.number_input("Max Calls", min_value=1, value=20, step=1)
with col2:
    max_in = st.number_input("Max Input Tokens", min_value=1000, value=200000, step=1000)
with col3:
    max_out = st.number_input("Max Output Tokens", min_value=1000, value=200000, step=1000)
with col4:
    reset_period = st.selectbox("Reset Period", ["daily", "monthly"], index=0)

save_budget_col, refresh_budget_col = st.columns([1, 1])
with save_budget_col:
    if st.button("Save Budget Limits"):
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
        out = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        st.code((out.stdout or "") + (out.stderr or ""))

with refresh_budget_col:
    if st.button("Refresh Remaining Budget"):
        cmd = ["python", "main.py", "show-ai-budget", "--ui-lang", ui_lang]
        out = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        st.code((out.stdout or "") + (out.stderr or ""))

# Always display current budget snapshot on page load
st.caption("Current budget snapshot")
auto_budget = subprocess.run(
    ["python", "main.py", "show-ai-budget", "--ui-lang", ui_lang],
    cwd=ROOT,
    capture_output=True,
    text=True,
)
st.code((auto_budget.stdout or "") + (auto_budget.stderr or ""))

st.subheader("Problem Filters")
difficulty = st.text_input("Difficulty", value="EASY,MEDIUM")
tags = st.text_input("Tags", value="")
limit = st.number_input("Fetch Limit", min_value=1, max_value=200, value=30, step=1)
pick = st.number_input("Pick Row #", min_value=1, value=1, step=1)

require_estimate = st.checkbox("Require token estimate before AI call", value=True)

st.markdown("### Step 1: Estimate")
if st.button("Estimate Tokens for This Run"):
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
    est_out = subprocess.run(est_cmd, cwd=ROOT, capture_output=True, text=True)
    st.code((est_out.stdout or "") + (est_out.stderr or ""))
    st.session_state.estimate_ready = True
    st.session_state.last_params = {
        "difficulty": difficulty.strip(),
        "tags": tags.strip(),
        "limit": int(limit),
        "pick": int(pick),
        "ui_lang": ui_lang,
    }

st.markdown("### Step 2: Generate")
if require_estimate and not st.session_state.estimate_ready:
    st.info("Please run token estimate first.")

if st.button("One-click Generate AI Best Solution", type="primary"):
    if not api_key.strip():
        st.error("Please input API Key first.")
    else:
        if require_estimate and not st.session_state.estimate_ready:
            st.error("Token estimate is required before generation.")
        else:
            current_params = {
                "difficulty": difficulty.strip(),
                "tags": tags.strip(),
                "limit": int(limit),
                "pick": int(pick),
                "ui_lang": ui_lang,
            }
            if require_estimate and current_params != st.session_state.last_params:
                st.error("Filters changed after estimate. Please estimate again.")
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
                out = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
                full = (out.stdout or "") + (out.stderr or "")
                if out.returncode == 0:
                    st.success("Generated successfully.")
                    st.code(full)
                    st.session_state.estimate_ready = False
                else:
                    st.error("Generation failed.")
                    st.code(full)

st.markdown("---")
st.caption("Start web UI with: streamlit run app.py")
