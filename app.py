import subprocess
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).parent

st.set_page_config(page_title="Brush Script AI Fallback", layout="wide")
st.title("Brush Script - One Click AI Best-Solution Fallback")

st.caption("选择题目筛选条件，输入 API Key，点击按钮一键生成 AI 参考最优解（最小时间复杂度优先）。")

with st.sidebar:
    st.header("API / Model")
    api_key = st.text_input("OpenAI API Key", type="password", placeholder="sk-...")
    model = st.text_input("Model", value="gpt-5.3")
    lang = st.selectbox("Code Language", ["python3", "cpp", "java"], index=0)
    ui_lang = st.selectbox("UI Language", ["en", "zh"], index=0)

st.subheader("Budget Limits (anti-overspending)")
col1, col2, col3 = st.columns(3)
with col1:
    max_calls = st.number_input("Max Calls", min_value=1, value=20, step=1)
with col2:
    max_in = st.number_input("Max Input Tokens", min_value=1000, value=200000, step=1000)
with col3:
    max_out = st.number_input("Max Output Tokens", min_value=1000, value=200000, step=1000)

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
        "--ui-lang",
        ui_lang,
    ]
    out = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    st.code((out.stdout or "") + (out.stderr or ""))

st.subheader("Problem Filters")
difficulty = st.text_input("Difficulty", value="EASY,MEDIUM")
tags = st.text_input("Tags", value="")
limit = st.number_input("Fetch Limit", min_value=1, max_value=200, value=30, step=1)
pick = st.number_input("Pick Row #", min_value=1, value=1, step=1)

if st.button("One-click Generate AI Best Solution", type="primary"):
    if not api_key.strip():
        st.error("Please input API Key first.")
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
        out = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        full = (out.stdout or "") + (out.stderr or "")
        if out.returncode == 0:
            st.success("Generated successfully.")
            st.code(full)
        else:
            st.error("Generation failed.")
            st.code(full)

st.markdown("---")
st.caption("Start web UI with: streamlit run app.py")
