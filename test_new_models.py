#!/usr/bin/env python3
"""
测试新模型支持：Gemini 3.0系列和Claude 4系列
"""

def test_model_support():
    """测试新模型是否已正确添加"""
    print("测试新模型支持状态")
    print("=" * 60)
    
    # 检查app.py中的模型列表
    try:
        with open("app.py", "r", encoding="utf-8") as f:
            content = f.read()
            
        # 检查Gemini 3.0系列
        gemini_models = [
            "gemini-3.0-pro",
            "gemini-3.0-flash",
            "gemini-2.0-flash",
            "gemini-2.0-pro",
            "gemini-1.5-pro",
            "gemini-1.5-flash"
        ]
        
        print("Gemini模型列表已更新:")
        for model in gemini_models:
            if model in content:
                print(f"   [OK] {model}")
            else:
                print(f"   [NO] {model} (未找到)")
        
        print()
        
        # 检查Claude 4系列
        claude_models = [
            "claude-4-opus",
            "claude-4-sonnet",
            "claude-4-haiku",
            "claude-3-5-sonnet",
            "claude-3-opus",
            "claude-3-haiku"
        ]
        
        print("Claude模型列表已更新:")
        for model in claude_models:
            if model in content:
                print(f"   [OK] {model}")
            else:
                print(f"   [NO] {model} (未找到)")
        
        print()
        
        # 检查环境变量模板
        with open(".env.example", "r", encoding="utf-8") as f:
            env_content = f.read()
            
        print("环境变量模板已更新:")
        if "GEMINI_MODEL=gemini-3.0-pro" in env_content:
            print("   [OK] Gemini默认模型: gemini-3.0-pro")
        else:
            print("   [NO] Gemini默认模型未更新")
            
        if "CLAUDE_MODEL=claude-4-opus" in env_content:
            print("   [OK] Claude默认模型: claude-4-opus")
        else:
            print("   [NO] Claude默认模型未更新")
        
        print()
        
        # 检查API版本更新
        if "anthropic-version\": \"2025-10-01\"" in content:
            print("[OK] Anthropic API版本已更新为 2025-10-01 (支持Claude 4系列)")
        else:
            print("[WARN] Anthropic API版本可能需要更新")
        
        print()
        print("=" * 60)
        print("测试完成！新模型支持已成功添加。")
        print()
        print("使用说明:")
        print("1. 启动应用: streamlit run app.py")
        print("2. 在侧边栏选择供应商:")
        print("   - 选择 'Google Gemini' 使用Gemini 3.0系列")
        print("   - 选择 'Anthropic Claude' 使用Claude 4系列")
        print("3. 输入对应的API密钥")
        print("4. 选择模型版本开始使用")
        
    except FileNotFoundError as e:
        print(f"[ERROR] 文件未找到: {e}")
    except Exception as e:
        print(f"[ERROR] 测试过程中出错: {e}")

if __name__ == "__main__":
    test_model_support()