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
st.caption(t("启动方式：streamlit run app.py", "Start web UI with: streamlit run app.py", ui_lang))
