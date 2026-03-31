#!/usr/bin/env python3
"""
测试模式切换功能的简单脚本
"""

import subprocess
import time
from pathlib import Path

def test_mode_switch():
    """测试Streamlit应用的模式切换功能"""
    print("🚀 启动Brush Script Web界面测试...")
    print("=" * 60)
    
    # 检查必要的文件
    required_files = ["app.py", "main.py", "requirements.txt"]
    for file in required_files:
        if not Path(file).exists():
            print(f"❌ 缺少必要文件: {file}")
            return False
    
    print("✅ 所有必要文件都存在")
    
    # 检查Python环境
    try:
        import streamlit
        print("✅ Streamlit已安装")
    except ImportError:
        print("❌ Streamlit未安装，请运行: pip install -r requirements.txt")
        return False
    
    # 显示使用说明
    print("\n📋 使用说明:")
    print("1. 在终端中运行: streamlit run app.py")
    print("2. 浏览器会自动打开 http://localhost:8501")
    print("3. 在侧边栏选择工作模式:")
    print("   - AI参考解生成: 生成AI最优解")
    print("   - 模拟面试评估: 评估代码面试表现")
    print("   - 刷题训练: 预留功能")
    print("\n🎯 新功能亮点:")
    print("• 侧边栏模式切换器")
    print("• 优化的界面布局")
    print("• 更好的用户体验")
    print("• 清晰的模式区分")
    
    print("\n" + "=" * 60)
    print("✅ 测试准备完成！")
    print("💡 提示: 确保已配置 .env 文件中的 LEETCODE_COOKIE")
    
    return True

if __name__ == "__main__":
    test_mode_switch()