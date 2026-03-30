# Brush Script 项目总览

> 一个面向 LeetCode（`leetcode.cn`）的**学习辅助自动化脚本**项目。
> 核心目标：帮你更高效地“选题-拆解-练习-复盘”，而不是替你一键提交。

---

## 1. 这个项目是什么？

`Brush Script` 是一个本地命令行工具（Python），用于优化刷题流程中的重复劳动：

- 拉取账号可见题目列表
- 识别并筛选未完成题目
- 根据难度/标签做定向练习
- 自动推荐下一题（减少“选题焦虑”）
- 为单题生成学习文档 + 代码模板 + 测试骨架
- 记录刷题日志，便于复盘与长期统计

它的定位是“学习流程助手”，不是“自动答题提交器”。

---

## 2. 适合谁用？

- 想稳定刷题、但不想每次手动找题的人
- 想做“按标签/难度专项训练”的人
- 想保留刷题过程沉淀（思路、错因、耗时）的同学
- 想把刷题变成可追踪、可复盘流程的人

---

## 3. 核心功能清单

### 3.1 题目获取与筛选

- 从 `leetcode.cn` 拉取题目列表
- 自动筛出“未完成题目”（未 AC）
- 支持参数筛选：
  - `--difficulty EASY,MEDIUM,HARD`
  - `--tags array,hash-table`
  - `--limit 50`

### 3.2 题目准备（prepare）

对指定题目自动生成三类文件：

1. `plans/*.md`：
   - 题目信息
   - “最小复杂度优先”思路草案
   - 复杂度分析模板
   - 易错点与自测清单

2. `solutions/*.py`：
   - 本地代码模板（默认 `python3`）

3. `tests/test_*.py`：
   - 测试骨架（基础样例 + 边界样例入口）

### 3.3 自动推荐（recommend）

根据你的筛选条件，自动推荐下一题：

- 先取未完成题目
- 难度优先级：`EASY > MEDIUM > HARD`
- 同难度下优先题号更小
- 推荐后自动生成学习文件（plan/solution/test）

### 3.4 登录状态校验（check-auth）

- 一键检查 `.env` 中的 `LEETCODE_COOKIE` 是否有效
- 若失效可及时提醒你重新登录并更新 Cookie

### 3.5 学习日志（log）

- 记录通过率、耗时、错因
- 追加写入 `logs/practice_log.jsonl`
- 便于你按周/月做复盘

### 3.6 AI 参考解（最小复杂度优先）

- 支持 AI 实时生成“参考最优解”（最小时间复杂度优先）
- 默认受预算管控，避免过度消耗
- 输出为学习参考 Markdown，不建议直接提交

### 3.7 预算管理与预估

- 支持查看实时剩余额度（CLI + Web）
- 每次调用前可进行 token 预估并确认
- 支持日 / 月自动重置预算窗口

### 3.8 终端显示优化

- 启动时尝试自动配置 UTF-8 输出
- 支持 UI 语言切换：`--ui-lang auto|en|cn`
- Windows 终端乱码时可强制 `--ui-lang en`

---

## 4. 工作流（推荐实践）

建议每次刷题按以下 6 步：

1. **校验登录态**
   - `python main.py check-auth`

2. **查看预算状态（若使用 AI）**
   - `python main.py show-ai-budget`

3. **选题**
   - 手动看列表：`python main.py list ...`
   - 或自动推荐：`python main.py recommend ...`

4. **生成学习文件**
   - 常规：`prepare` / `recommend`
   - 卡住时：`fallback-solve`
   - 最后兜底：`ai-fallback`

5. **AI 调用前先预估（推荐）**
   - `python main.py estimate-ai-fallback ...`
   - 根据预估确认是否继续

6. **记录复盘**
   - `python main.py log --pass-rate ... --spent-min ... --cause "..."`

这样做可以形成稳定的“输入-训练-反馈”闭环。

---

## 5. 快速开始（从 0 到可用）

### 5.1 安装依赖

```bash
pip install -r requirements.txt
```

### 5.2 配置环境变量

```bash
copy .env.example .env
```

打开 `.env`，填写：

```env
LEETCODE_COOKIE=LEETCODE_SESSION=xxxx; csrftoken=yyyy; ...
DEFAULT_LANG=python3
DEFAULT_LIMIT=10
```

### 5.3 验证

```bash
python main.py check-auth --ui-lang en
```

如果显示已登录，即配置成功。

---

## 6. 常用命令速查

### 6.1 列表

```bash
python main.py list --difficulty EASY,MEDIUM --tags array,hash-table --limit 30
```

### 6.2 生成指定题目学习文件

```bash
python main.py prepare --difficulty MEDIUM --tags array --limit 20 --pick 1 --open
```

### 6.3 自动推荐下一题

```bash
python main.py recommend --difficulty EASY,MEDIUM --tags array --limit 50 --open
```

### 6.4 AI 预算设置（含重置周期）

```bash
python main.py set-ai-budget --max-calls 20 --max-input-tokens 200000 --max-output-tokens 200000 --reset-period daily
```

可选：`--reset-period monthly`

### 6.5 查看实时剩余额度

```bash
python main.py show-ai-budget
```

### 6.6 调用前 token 预估

```bash
python main.py estimate-ai-fallback --difficulty EASY,MEDIUM --tags array --limit 30 --pick 1
```

### 6.7 AI 最终兜底参考生成

```bash
python main.py ai-fallback --difficulty EASY,MEDIUM --tags array --limit 30 --pick 1
```

### 6.8 记录日志

```bash
python main.py log --pass-rate 0.8 --spent-min 32 --cause "边界条件漏处理"
```

### 6.9 语言与显示

```bash
python main.py list --ui-lang auto
python main.py list --ui-lang en
python main.py list --ui-lang cn
```

---

## 7. 目录结构说明

```text
Brush_Script/
├─ main.py                # 主程序入口（命令行）
├─ config.json            # 项目配置（目录/策略等）
├─ .env.example           # 环境变量模板
├─ requirements.txt       # 依赖列表
├─ README.md              # 快速使用文档
├─ PROJECT_OVERVIEW.md    # 本总览文档
├─ app.py                 # Streamlit 可视化一键界面
├─ plans/                 # 每题学习思路文档
├─ solutions/             # 每题代码模板/实现
├─ tests/                 # 每题测试骨架/自测
└─ logs/                  # 训练日志（含 ai_budget.json）
```

> `plans/solutions/tests/logs` 会在首次运行时自动创建。

---

## 8. 安全与边界

1. **Cookie 安全**
   - `LEETCODE_COOKIE` 属于敏感信息
   - 不要提交到公开仓库
   - 建议把 `.env` 加入 `.gitignore`

2. **学习边界**
   - 项目仅辅助流程，不替代独立思考
   - 默认保留人工确认步骤（打开页面/粘贴/提交）

3. **接口稳定性**
   - 若 LeetCode 页面或接口变更，脚本可能需要适配更新

---

## 9. 常见问题（FAQ）

### Q1：为什么中文在终端里是乱码？
A：Windows 控制台编码/字体可能与 UTF-8 不一致。可直接使用：

```bash
python main.py list --ui-lang en
```

### Q2：`check-auth` 失败怎么办？
A：通常是 Cookie 过期或复制不完整。重新登录 `leetcode.cn` 后重新复制请求头中的 cookie 到 `.env`。

### Q3：为什么推荐题目和我预期不一致？
A：推荐规则当前是“未做 + 难度优先 + 题号优先”。你可以通过 `--difficulty` 和 `--tags` 精确约束候选范围。

---

## 10. Win11 App 路线规划（B→A）

**当前策略：先做方案 B，再做方案 A。**

- **方案 B（已完成，可直接用）**：双击启动 Web UI（`run_brush_app.bat` / `run_brush_app.ps1`），自动打开浏览器。
- **方案 A（已进入实施）**：在不改核心逻辑前提下，增加 EXE 打包与启动链路。
  - 已新增：`launcher.py`（EXE 启动入口）
  - 已新增：`BrushScriptApp.spec`（PyInstaller 打包配置）
  - 已新增：`build_exe.ps1`（一键打包脚本）
  - 已新增：`run_brush_app_exe.bat`（EXE 启动器）
  - 已完成：完整打包实测（产物位于 `dist/BrushScriptApp/`）
  - 已完成：分发目录整理脚本（`release.ps1` / `release.bat`）

执行方式：

```powershell
powershell -ExecutionPolicy Bypass -File build_exe.ps1
```

```bash
run_brush_app_exe.bat
```

发布包整理（最小可分发目录）：

```powershell
powershell -ExecutionPolicy Bypass -File release.ps1 -Clean
```

或双击：`release.bat`

`release/` 中保留：
- `BrushScriptApp.exe`
- `_internal/`
- `.env.example`
- `README.md`
- `PROJECT_OVERVIEW.md`

该路线能保证：
- 先快速可用（B）
- 后续升级为桌面 App 时不需要重写核心逻辑（A）

---

## 11. 后续扩展方向（建议）

- 统计仪表盘：按标签/难度/周维度展示训练趋势
- 错因分类体系：审题、边界、复杂度、实现细节等
- 本地数据库（SQLite）持久化题目训练状态
- 针对不同语言生成更贴近官方函数签名的模板
- 训练计划模式（例如 30 天算法专项）

---

## 11. 一句话总结

`Brush Script` 把刷题从“临时行为”变成“可管理的学习系统”：

**自动选题 + 结构化练习 + 数据化复盘**，提高效率，也提高长期进步的确定性。
