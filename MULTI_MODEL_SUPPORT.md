# Brush Script - 多模型支持更新说明

## 🎯 更新概述

本次更新为Brush Script添加了多AI模型供应商支持，使应用能够接入DeepSeek-V3.2、Google Gemini、Anthropic Claude等多种AI模型，不再局限于OpenAI GPT系列。

## 🔧 新增功能

### 1. 多供应商API支持
- **OpenAI**: GPT-5.3, GPT-4o, GPT-4-turbo, GPT-3.5-turbo
- **DeepSeek**: deepseek-v3.2, deepseek-chat, deepseek-coder
- **Google Gemini**: gemini-3.0-pro, gemini-3.0-flash, gemini-2.0-flash, gemini-2.0-pro, gemini-1.5-pro, gemini-1.5-flash
- **Anthropic Claude**: claude-4-opus, claude-4-sonnet, claude-4-haiku, claude-3-5-sonnet, claude-3-opus, claude-3-haiku
- **自定义API**: 支持任意兼容OpenAI格式的API

### 2. 界面改进
- **侧边栏供应商选择器**: 直观的供应商切换界面
- **动态配置表单**: 根据供应商显示相应的API密钥格式
- **统一的基础URL管理**: 支持自定义API端点

### 3. 环境变量支持
新增以下环境变量：
```env
# 默认供应商
AI_PROVIDER=openai
AI_BASE_URL=

# 各供应商API密钥
OPENAI_API_KEY=
DEEPSEEK_API_KEY=
GEMINI_API_KEY=
CLAUDE_API_KEY=

# 各供应商默认模型
OPENAI_MODEL=gpt-5.3
DEEPSEEK_MODEL=deepseek-v3.2
GEMINI_MODEL=gemini-3.0-pro
CLAUDE_MODEL=claude-4-opus
```

## 🚀 使用指南

### 1. 配置环境变量
复制并更新 `.env` 文件：
```bash
cp .env.example .env
```

编辑 `.env` 文件，填写您选择的供应商API密钥。

### 2. Web界面使用
1. 启动应用：`streamlit run app.py`
2. 在侧边栏选择AI供应商
3. 输入对应的API密钥
4. 选择模型版本
5. 开始使用AI参考解生成或模拟面试评估

### 3. 命令行使用
新增命令行参数：
```bash
# 指定供应商
python main.py ai-fallback --provider deepseek --api-key YOUR_DEEPSEEK_KEY

# 指定自定义API
python main.py ai-fallback --provider custom --base-url https://api.example.com/v1

# 模拟面试评估
python main.py ai-interview-eval --provider gemini --slug two-sum --code solution.py
```

## 📁 修改的文件

### 核心文件
1. **`app.py`** - Web界面重构
   - 添加供应商选择器
   - 动态API配置表单
   - 供应商状态管理

2. **`main.py`** - 后端逻辑重构
   - 新增 `AIClient` 通用类
   - 支持多种API格式（OpenAI、Gemini、Claude）
   - 更新命令行参数解析

3. **`.env.example`** - 环境变量模板
   - 添加多供应商配置
   - 统一的环境变量命名

### 辅助文件
4. **`MULTI_MODEL_SUPPORT.md`** - 本文档
5. **`quick_test.html`** - 界面预览

## 🔌 API兼容性

### OpenAI兼容格式
- 支持所有兼容OpenAI API格式的服务
- 包括：OpenAI、DeepSeek、自定义部署等

### Google Gemini格式
- 使用Google Generative Language API
- 自动处理API密钥和请求格式

### Anthropic Claude格式
- 使用Anthropic Messages API
- 支持Claude 3系列模型

### 自定义API
- 支持任意兼容OpenAI格式的API
- 可自定义基础URL和模型名称

## 💡 使用建议

### 1. 性能考虑
- **DeepSeek**: 性价比高，中文支持好
- **Gemini**: 响应速度快，免费额度充足
- **Claude**: 推理能力强，适合复杂问题
- **OpenAI**: 功能全面，生态完善

### 2. 成本控制
- 使用 `set-ai-budget` 设置预算上限
- 不同供应商的token定价不同
- 建议根据使用频率选择合适的供应商

### 3. 故障切换
- 配置多个供应商的API密钥
- 在主供应商故障时可快速切换
- 所有功能都支持供应商切换

## 🐛 已知问题与限制

1. **Gemini API限制**: 某些地区可能需要代理
2. **Claude上下文长度**: 注意不同模型的token限制
3. **响应格式差异**: 不同供应商的响应格式可能略有不同
4. **错误处理**: 部分供应商的错误信息可能不够详细

## 🔮 未来规划

1. **供应商自动检测**: 根据API密钥自动识别供应商
2. **模型性能对比**: 不同模型在算法题上的表现对比
3. **混合模型策略**: 根据题目难度自动选择最佳模型
4. **本地模型支持**: 集成Ollama等本地模型部署

## 📞 技术支持

如遇到问题，请：
1. 检查API密钥是否正确
2. 确认供应商服务状态
3. 查看错误日志信息
4. 参考各供应商官方文档

---

**版本**: 2.1 (多模型支持版)
**更新日期**: 2026-03-31
**兼容性**: 向后兼容原有OpenAI配置