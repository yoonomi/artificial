#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AutoGen 知识图谱API测试脚本

测试三个核心API端点：
1. POST /api/start-analysis - 启动文本分析
2. GET /api/analysis-status/{task_id} - 获取任务状态
3. GET /api/graph-data/{task_id} - 获取图谱数据
"""

import requests
import json
import time
import sys
from typing import Dict, Any

# API基础URL
BASE_URL = "http://localhost:8000"

def print_section(title: str):
    """打印分节标题"""
    print(f"\n{'='*50}")
    print(f"🧪 {title}")
    print(f"{'='*50}")

def print_step(step: str):
    """打印步骤信息"""
    print(f"\n📋 {step}")
    print("-" * 40)

def print_success(message: str):
    """打印成功信息"""
    print(f"✅ {message}")

def print_error(message: str):
    """打印错误信息"""
    print(f"❌ {message}")

def print_info(message: str):
    """打印信息"""
    print(f"ℹ️  {message}")

def print_json(data: Dict[Any, Any], title: str = "响应数据"):
    """格式化打印JSON数据"""
    print(f"\n📄 {title}:")
    print(json.dumps(data, ensure_ascii=False, indent=2))

def test_health_check():
    """测试健康检查端点"""
    print_step("测试健康检查端点")
    
    try:
        response = requests.get(f"{BASE_URL}/api/health")
        
        if response.status_code == 200:
            data = response.json()
            print_success("健康检查通过")
            print_json(data, "健康状态")
            return True
        else:
            print_error(f"健康检查失败: HTTP {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print_error("无法连接到API服务，请确保服务正在运行")
        print_info("启动命令: python api/main.py")
        return False
    except Exception as e:
        print_error(f"健康检查异常: {str(e)}")
        return False

def test_start_analysis():
    """测试启动分析端点"""
    print_step("测试启动文本分析")
    
    # 测试文本
    test_text = """
    人工智能（Artificial Intelligence, AI）是计算机科学的一个分支，旨在创建能够执行通常需要人类智能的任务的系统。
    机器学习是人工智能的一个重要子领域，通过算法让计算机从数据中学习。
    深度学习是机器学习的一个分支，使用神经网络来模拟人脑的工作方式。
    OpenAI是一家专注于人工智能研究的公司，开发了GPT系列模型。
    GPT是生成式预训练Transformer模型，能够理解和生成自然语言文本。
    """
    
    try:
        payload = {"text": test_text.strip()}
        response = requests.post(f"{BASE_URL}/api/start-analysis", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            print_success("文本分析任务创建成功")
            print_json(data, "任务响应")
            return data.get("task_id")
        else:
            print_error(f"任务创建失败: HTTP {response.status_code}")
            print(response.text)
            return None
            
    except Exception as e:
        print_error(f"启动分析异常: {str(e)}")
        return None

def test_analysis_status(task_id: str):
    """测试获取分析状态"""
    print_step("测试获取任务状态")
    
    if not task_id:
        print_error("无效的任务ID")
        return False
    
    try:
        # 轮询任务状态直到完成
        max_attempts = 30  # 最多等待30次
        for attempt in range(max_attempts):
            response = requests.get(f"{BASE_URL}/api/analysis-status/{task_id}")
            
            if response.status_code == 200:
                data = response.json()
                status = data.get("status")
                progress = data.get("progress", 0)
                message = data.get("message", "")
                
                print(f"📊 尝试 {attempt + 1}/{max_attempts} - 状态: {status} ({progress}%) - {message}")
                
                if status == "COMPLETED":
                    print_success("任务完成")
                    print_json(data, "最终状态")
                    return True
                elif status == "FAILED":
                    print_error("任务失败")
                    print_json(data, "失败信息")
                    return False
                elif status in ["PENDING", "PROCESSING"]:
                    time.sleep(2)  # 等待2秒后重试
                    continue
                else:
                    print_error(f"未知状态: {status}")
                    return False
            else:
                print_error(f"状态查询失败: HTTP {response.status_code}")
                print(response.text)
                return False
        
        print_error("任务超时，超过最大等待时间")
        return False
        
    except Exception as e:
        print_error(f"状态查询异常: {str(e)}")
        return False

def test_graph_data(task_id: str):
    """测试获取图谱数据"""
    print_step("测试获取图谱数据")
    
    if not task_id:
        print_error("无效的任务ID")
        return False
    
    try:
        response = requests.get(f"{BASE_URL}/api/graph-data/{task_id}")
        
        if response.status_code == 200:
            data = response.json()
            print_success("图谱数据获取成功")
            
            nodes = data.get("nodes", [])
            edges = data.get("edges", [])
            metadata = data.get("metadata", {})
            
            print(f"📊 节点数量: {len(nodes)}")
            print(f"🔗 边数量: {len(edges)}")
            print(f"📈 元数据: {metadata}")
            
            # 显示前5个节点和边的详细信息
            if nodes:
                print("\n🔵 前5个节点:")
                for i, node in enumerate(nodes[:5]):
                    print(f"  {i+1}. {node.get('label', 'N/A')} (ID: {node.get('id', 'N/A')})")
            
            if edges:
                print("\n🔗 前5个关系:")
                for i, edge in enumerate(edges[:5]):
                    print(f"  {i+1}. {edge.get('source', 'N/A')} -[{edge.get('label', 'N/A')}]-> {edge.get('target', 'N/A')}")
            
            # 保存完整数据到文件
            with open("test_graph_data.json", "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print_info("完整图谱数据已保存到 test_graph_data.json")
            
            return True
        else:
            print_error(f"图谱数据获取失败: HTTP {response.status_code}")
            print(response.text)
            return False
            
    except Exception as e:
        print_error(f"图谱数据获取异常: {str(e)}")
        return False

def test_error_cases():
    """测试错误情况"""
    print_step("测试错误处理")
    
    test_cases = [
        {
            "name": "无效任务ID格式",
            "url": f"{BASE_URL}/api/analysis-status/invalid-uuid",
            "expected_status": 400
        },
        {
            "name": "不存在的任务ID", 
            "url": f"{BASE_URL}/api/analysis-status/550e8400-e29b-41d4-a716-446655440000",
            "expected_status": 404
        },
        {
            "name": "空文本分析",
            "url": f"{BASE_URL}/api/start-analysis",
            "method": "POST",
            "data": {"text": ""},
            "expected_status": 422
        }
    ]
    
    for case in test_cases:
        print(f"\n🔍 测试: {case['name']}")
        try:
            if case.get("method") == "POST":
                response = requests.post(case["url"], json=case.get("data", {}))
            else:
                response = requests.get(case["url"])
            
            if response.status_code == case["expected_status"]:
                print_success(f"错误处理正确 (HTTP {response.status_code})")
            else:
                print_error(f"期望状态码 {case['expected_status']}, 实际 {response.status_code}")
                
        except Exception as e:
            print_error(f"测试异常: {str(e)}")

def run_comprehensive_test():
    """运行完整的API测试"""
    print_section("AutoGen 知识图谱API 综合测试")
    
    # 1. 健康检查
    if not test_health_check():
        print_error("API服务未启动，测试中止")
        return False
    
    # 2. 启动分析
    task_id = test_start_analysis()
    if not task_id:
        print_error("无法创建分析任务，测试中止")
        return False
    
    # 3. 监控状态
    if not test_analysis_status(task_id):
        print_error("任务状态监控失败")
        return False
    
    # 4. 获取图谱数据
    if not test_graph_data(task_id):
        print_error("图谱数据获取失败")
        return False
    
    # 5. 错误情况测试
    test_error_cases()
    
    print_section("测试完成")
    print_success("所有核心功能测试通过！")
    print_info("API服务正常工作，可以进行前后端集成")
    
    return True

def main():
    """主函数"""
    if len(sys.argv) > 1:
        if sys.argv[1] == "health":
            test_health_check()
        elif sys.argv[1] == "analysis":
            task_id = test_start_analysis()
            if task_id:
                test_analysis_status(task_id)
                test_graph_data(task_id)
        elif sys.argv[1] == "errors":
            test_error_cases()
        else:
            print("使用方式:")
            print("  python test_api.py           # 运行完整测试")
            print("  python test_api.py health    # 仅测试健康检查")
            print("  python test_api.py analysis  # 仅测试分析流程")
            print("  python test_api.py errors    # 仅测试错误处理")
    else:
        run_comprehensive_test()

if __name__ == "__main__":
    main() 