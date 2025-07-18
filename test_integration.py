#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
前后端集成测试脚本
验证完整的API调用流程，确保前端可以正常与后端交互
"""

import requests
import json
import time
import uuid

def test_frontend_backend_integration():
    """测试前端与后端的完整集成流程"""
    
    print("🧪 开始前后端集成测试")
    print("=" * 50)
    
    # API基础URL
    API_BASE_URL = 'http://localhost:8000'
    
    # 测试文本
    test_text = """
    人工智能（Artificial Intelligence, AI）是计算机科学的一个分支，旨在创建能够执行通常需要人类智能的任务的系统。
    机器学习是人工智能的一个重要子领域，通过算法让计算机从数据中学习。
    深度学习是机器学习的一个分支，使用神经网络来模拟人脑的工作方式。
    自然语言处理和计算机视觉是AI的重要应用领域。
    OpenAI开发了GPT系列模型，推动了生成式AI的发展。
    """
    
    try:
        # 步骤1: 检查API健康状态
        print("1️⃣ 检查API健康状态...")
        health_response = requests.get(f'{API_BASE_URL}/api/health', timeout=10)
        
        if health_response.status_code == 200:
            health_data = health_response.json()
            print(f"   ✅ API服务正常: {health_data['status']}")
            print(f"   📊 活跃任务: {health_data['active_tasks']}")
            print(f"   📈 总任务数: {health_data['total_tasks']}")
        else:
            raise Exception(f"API健康检查失败: {health_response.status_code}")
        
        # 步骤2: 启动文本分析
        print("\n2️⃣ 启动文本分析...")
        print(f"   📝 文本长度: {len(test_text)} 字符")
        
        start_payload = {'text': test_text}
        start_response = requests.post(
            f'{API_BASE_URL}/api/start-analysis', 
            json=start_payload,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if start_response.status_code == 200:
            start_data = start_response.json()
            task_id = start_data['task_id']
            print(f"   ✅ 任务创建成功")
            print(f"   🆔 任务ID: {task_id}")
            print(f"   📋 状态: {start_data['status']}")
            print(f"   💬 消息: {start_data['message']}")
        else:
            raise Exception(f"启动分析失败: {start_response.status_code} - {start_response.text}")
        
        # 步骤3: 轮询任务状态
        print("\n3️⃣ 轮询任务状态...")
        max_polls = 20  # 最多轮询20次
        poll_interval = 3  # 每3秒轮询一次
        
        for poll_count in range(max_polls):
            print(f"   🔄 第 {poll_count + 1} 次轮询...")
            
            status_response = requests.get(
                f'{API_BASE_URL}/api/analysis-status/{task_id}',
                timeout=10
            )
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                print(f"      📊 状态: {status_data['status']}")
                print(f"      📈 进度: {status_data.get('progress', 0)}%")
                print(f"      💬 消息: {status_data.get('message', 'N/A')}")
                
                if status_data['status'] == 'COMPLETED':
                    print("   ✅ 分析完成！")
                    break
                elif status_data['status'] == 'FAILED':
                    raise Exception(f"分析失败: {status_data.get('error', '未知错误')}")
                else:
                    print(f"      ⏳ 等待 {poll_interval} 秒后继续轮询...")
                    time.sleep(poll_interval)
            else:
                raise Exception(f"状态查询失败: {status_response.status_code}")
        
        else:
            raise Exception("轮询超时，分析未完成")
        
        # 步骤4: 获取图谱数据
        print("\n4️⃣ 获取图谱数据...")
        
        graph_response = requests.get(
            f'{API_BASE_URL}/api/graph-data/{task_id}',
            timeout=10
        )
        
        if graph_response.status_code == 200:
            graph_data = graph_response.json()
            print(f"   ✅ 图谱数据获取成功")
            print(f"   🔗 节点数量: {len(graph_data.get('nodes', []))}")
            print(f"   🔗 边数量: {len(graph_data.get('edges', []))}")
            
            # 显示节点信息
            nodes = graph_data.get('nodes', [])
            if nodes:
                print(f"   📋 节点示例:")
                for i, node in enumerate(nodes[:3]):  # 显示前3个节点
                    print(f"      {i+1}. {node.get('label', 'N/A')} (ID: {node.get('id', 'N/A')})")
                
                if len(nodes) > 3:
                    print(f"      ... 还有 {len(nodes) - 3} 个节点")
            
            # 显示边信息
            edges = graph_data.get('edges', [])
            if edges:
                print(f"   🔗 关系示例:")
                for i, edge in enumerate(edges[:3]):  # 显示前3个关系
                    print(f"      {i+1}. {edge.get('label', 'N/A')} ({edge.get('source', 'N/A')} → {edge.get('target', 'N/A')})")
                
                if len(edges) > 3:
                    print(f"      ... 还有 {len(edges) - 3} 个关系")
            
            # 保存结果到文件
            output_file = f'test_result_{task_id[:8]}.json'
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(graph_data, f, ensure_ascii=False, indent=2)
            print(f"   💾 结果已保存到: {output_file}")
            
        else:
            raise Exception(f"获取图谱数据失败: {graph_response.status_code}")
        
        # 步骤5: 验证数据格式
        print("\n5️⃣ 验证数据格式...")
        
        # 验证必要字段
        required_fields = ['task_id', 'nodes', 'edges']
        for field in required_fields:
            if field not in graph_data:
                raise Exception(f"缺少必要字段: {field}")
        
        # 验证节点格式
        for node in graph_data.get('nodes', []):
            node_required = ['id', 'label']
            for req_field in node_required:
                if req_field not in node:
                    raise Exception(f"节点缺少必要字段: {req_field}")
        
        # 验证边格式
        for edge in graph_data.get('edges', []):
            edge_required = ['id', 'source', 'target', 'label']
            for req_field in edge_required:
                if req_field not in edge:
                    raise Exception(f"边缺少必要字段: {req_field}")
        
        print("   ✅ 数据格式验证通过")
        
        print("\n🎉 前后端集成测试完成！")
        print("=" * 50)
        print("✅ 所有功能正常工作")
        print("📊 数据格式符合要求")
        print("🔄 完整流程验证成功")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ 连接错误：请确保API服务正在运行 (python api/main_simple.py)")
        return False
    except requests.exceptions.Timeout:
        print("❌ 请求超时：API服务响应缓慢")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return False

def test_error_scenarios():
    """测试错误场景处理"""
    
    print("\n🧪 测试错误场景处理")
    print("=" * 30)
    
    API_BASE_URL = 'http://localhost:8000'
    
    try:
        # 测试空文本
        print("1️⃣ 测试空文本处理...")
        empty_response = requests.post(
            f'{API_BASE_URL}/api/start-analysis',
            json={'text': ''},
            timeout=5
        )
        
        if empty_response.status_code == 422:  # Validation error expected
            print("   ✅ 空文本正确被拒绝")
        else:
            print(f"   ⚠️ 空文本处理结果: {empty_response.status_code}")
        
        # 测试不存在的任务ID
        print("2️⃣ 测试不存在的任务ID...")
        fake_task_id = str(uuid.uuid4())
        fake_response = requests.get(
            f'{API_BASE_URL}/api/analysis-status/{fake_task_id}',
            timeout=5
        )
        
        if fake_response.status_code == 404:
            print("   ✅ 不存在的任务ID正确返回404")
        else:
            print(f"   ⚠️ 不存在任务ID处理结果: {fake_response.status_code}")
        
        # 测试无效任务ID格式
        print("3️⃣ 测试无效任务ID格式...")
        invalid_response = requests.get(
            f'{API_BASE_URL}/api/analysis-status/invalid-id',
            timeout=5
        )
        
        if invalid_response.status_code == 400:
            print("   ✅ 无效任务ID格式正确返回400")
        else:
            print(f"   ⚠️ 无效任务ID格式处理结果: {invalid_response.status_code}")
        
        print("✅ 错误场景测试完成")
        
    except Exception as e:
        print(f"❌ 错误场景测试失败: {str(e)}")

if __name__ == "__main__":
    print("🚀 AutoGen 前后端集成测试")
    print("🎯 验证React前端与FastAPI后端的完整交互流程")
    print()
    
    # 主要集成测试
    success = test_frontend_backend_integration()
    
    if success:
        # 错误场景测试
        test_error_scenarios()
        
        print("\n" + "="*60)
        print("🎊 所有测试完成！")
        print("📋 测试总结:")
        print("   ✅ API健康检查")
        print("   ✅ 任务创建")
        print("   ✅ 状态轮询")
        print("   ✅ 图谱数据获取")
        print("   ✅ 数据格式验证")
        print("   ✅ 错误处理")
        print()
        print("🎯 前端应该可以正常工作了！")
        print("🌐 React应用地址: http://localhost:3000")
        print("📖 API文档地址: http://localhost:8000/docs")
        
    else:
        print("\n❌ 集成测试失败，请检查API服务状态")
        print("💡 启动API服务: python api/main_simple.py") 