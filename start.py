#!/usr/bin/env python3
"""
TrendPulse 启动脚本
"""
import os
import sys
import argparse


def check_dependencies():
    """检查依赖是否安装"""
    try:
        import fastapi
        import sqlalchemy
        import httpx
        print("✅ 依赖检查通过")
        return True
    except ImportError as e:
        print(f"❌ 缺少依赖: {e}")
        print("请运行: pip install -r requirements.txt")
        return False


def init_config():
    """初始化配置文件"""
    if not os.path.exists("config.yaml"):
        if os.path.exists("config.yaml.example"):
            import shutil
            shutil.copy("config.yaml.example", "config.yaml")
            print("✅ 已创建配置文件: config.yaml")
            print("⚠️  请编辑 config.yaml 配置您的API密钥和通知渠道")
        else:
            print("❌ 未找到配置文件模板")
            return False
    return True


def main():
    parser = argparse.ArgumentParser(description="TrendPulse - 多平台热点聚合AI分析工具")
    parser.add_argument("--host", default="0.0.0.0", help="绑定地址 (默认: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8080, help="绑定端口 (默认: 8080)")
    parser.add_argument("--reload", action="store_true", help="启用热重载 (开发模式)")
    parser.add_argument("--init", action="store_true", help="仅初始化配置")
    
    args = parser.parse_args()
    
    # 检查依赖
    if not check_dependencies():
        sys.exit(1)
    
    # 初始化配置
    if not init_config():
        sys.exit(1)
    
    if args.init:
        print("✅ 初始化完成")
        return
    
    # 启动应用
    import uvicorn
    
    print(f"🚀 启动 TrendPulse...")
    print(f"📍 访问地址: http://{args.host}:{args.port}")
    
    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


if __name__ == "__main__":
    main()
