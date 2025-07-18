#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AutoGen 知识图谱API启动脚本
"""

import os
import sys
import subprocess
import time

def check_dependencies():
    """检查必要的依赖"""
    print("🔍 检查API依赖...")
    
    required_packages = [
        "fastapi",
        "uvicorn", 
        "pydantic",
        "requests"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package}")
    
    if missing_packages:
        print(f"\n⚠️  缺少依赖包: {', '.join(missing_packages)}")
        print("安装命令: pip install fastapi uvicorn pydantic requests")
        return False
    
    print("✅ 所有依赖已满足")
    return True

def start_api_server():
    """启动API服务器"""
    print("\n🚀 启动AutoGen知识图谱API服务...")
    
    # 确保在正确的目录
    project_root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_root)
    
    try:
        # 启动uvicorn服务器
        cmd = [
            sys.executable, "-m", "uvicorn", 
            "api.main:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload"
        ]
        
        print(f"执行命令: {' '.join(cmd)}")
        print("📖 API文档: http://localhost:8000/docs")
        print("🔍 ReDoc文档: http://localhost:8000/redoc")
        print("❤️‍🔥 健康检查: http://localhost:8000/api/health")
        print("\n按 Ctrl+C 停止服务")
        
        # 启动服务
        process = subprocess.run(cmd, check=True)
        
    except KeyboardInterrupt:
        print("\n🛑 服务已停止")
    except subprocess.CalledProcessError as e:
        print(f"❌ 启动失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 启动异常: {e}")
        return False
    
    return True

def test_api_connectivity():
    """测试API连通性"""
    print("\n🧪 测试API连通性...")
    
    import requests
    import time
    
    # 等待服务启动
    for attempt in range(10):
        try:
            response = requests.get("http://localhost:8000/api/health", timeout=5)
            if response.status_code == 200:
                print("✅ API服务正常运行")
                return True
        except:
            print(f"⏳ 等待服务启动... ({attempt + 1}/10)")
            time.sleep(2)
    
    print("❌ API服务连通性测试失败")
    return False

def main():
    """主函数"""
    print("=" * 60)
    print("🧠 AutoGen 知识图谱API服务启动器")
    print("=" * 60)
    
    # 检查依赖
    if not check_dependencies():
        sys.exit(1)
    
    # 启动服务
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # 仅测试模式
        if test_api_connectivity():
            print("🎉 API服务测试通过")
        else:
            print("💔 API服务测试失败")
            sys.exit(1)
    else:
        # 正常启动模式
        start_api_server()

if __name__ == "__main__":
    main() 