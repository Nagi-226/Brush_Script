# Brush Script（LeetCode 学习辅助自动化）

这是一个学习辅助脚本，支持普通刷题流程，也支持在你“实在解不出来”时通过 AI 一键生成参考最优解（最小时间复杂度优先）用于学习。

## 功能

- 未完成题目筛选（`list`）
- 手动准备学习文件（`prepare`）
- 自动推荐下一题（`recommend`）
- Cookie 校验（`check-auth`）
- 本地兜底模板（`fallback-solve`）
- **AI 实时兜底参考解（`ai-fallback`）**
- **调用上限设置防超支（`set-ai-budget`）**
- 做题日志（`log`）

---

## 安装

```bash
pip install -r requirements.txt
```

---

## 配置

```bash
copy .env.example .env
```

填写 `.env`：

```env
LEETCODE_COOKIE=LEETCODE_SESSION=xxxx; csrftoken=yyyy; ...
DEFAULT_LANG=python3
DEFAULT_LIMIT=10
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-5.3
```

---

## AI 防超支预算

设置调用上限（强烈建议先设置）：

```bash
python main.py set-ai-budget --max-calls 20 --max-input-tokens 200000 --max-output-tokens 200000
```

当达到任一上限时，`ai-fallback` 会被阻止继续调用。

---

## 一键 AI 参考最优解（CLI）

```bash
python main.py ai-fallback --difficulty EASY,MEDIUM --tags array,hash-table --limit 30 --pick 1 --force
```

说明：
- 会实时调用你配置的模型 API（消耗 token）
- 自动拉取题目详情并生成：策略说明 + 复杂度 + 边界 + 参考代码 + 测试
- 输出保存到：
  - `plans/ai_fallback_*.md`
  - `solutions/ai_fallback_*.md`

---

## 一键 AI 参考最优解（Web 按钮界面）

### Win11 双击启动（方案 B 推荐）

直接双击以下文件，会自动打开浏览器：

- `run_brush_app.bat`
- `run_brush_app.ps1`

### 方案 A（EXE 打包，下一阶段）

当前已准备好 EXE 构建脚本与启动器：

- `build_exe.ps1`：构建 `.exe`（基于 `BrushScriptApp.spec`）
- `run_brush_app_exe.bat`：双击后自动构建并启动

执行打包：

```powershell
powershell -ExecutionPolicy Bypass -File build_exe.ps1
```

启动已打包应用：

```bash
run_brush_app_exe.bat
```

如果 PowerShell 被执行策略拦截，可临时允许：

```powershell
Set-ExecutionPolicy -Scope Process Bypass
```

### 手动启动

```bash
streamlit run app.py
```

界面支持：
- 输入 API Key
- 选择模型
- 设置预算上限（调用次数/输入 token/输出 token）
- 实时显示剩余额度（可刷新）
- 调用前 token 预估 + 变更校验
- 填筛选条件和题目序号
- 点击 **One-click Generate AI Best Solution** 一键生成

---

## 常用命令

```bash
python main.py check-auth
python main.py list --difficulty EASY,MEDIUM --limit 30
python main.py recommend --difficulty EASY,MEDIUM --tags array --limit 30
python main.py prepare --pick 1
python main.py fallback-solve --pick 1 --force
python main.py log --pass-rate 0.8 --spent-min 30 --cause "boundary"
```

---

## 注意

- AI 结果是学习参考，不保证绝对理论最优或一次 AC。
- 请务必本地自测与人工校验。
- `.env` 含敏感信息，勿提交公开仓库。
