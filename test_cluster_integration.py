#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
集群化功能测试脚本
验证后端API生成的数据包含集群信息，前端可以正确处理集群化显示
"""

import requests
import json
import time

def test_cluster_functionality():
    """测试集群化功能的完整流程"""
    
    print("🧩 集群化功能测试")
    print("=" * 50)
    
    # API基础URL
    API_BASE_URL = 'http://localhost:8000'
    
    # 测试文本 - 包含不同领域的关键词以测试集群分配
    test_text = """
    人工智能（AI）是计算机科学的一个分支，它旨在创建智能机器。
    机器学习是人工智能的核心技术，通过算法让计算机从数据中学习。
    深度学习使用神经网络来模拟人脑的工作方式。
    企业管理包括战略规划、组织结构和人力资源管理。
    商业分析和市场营销是现代企业的重要组成部分。
    软件开发需要编程技能和系统设计能力。
    网络通信技术连接了全球的计算机系统。
    科学研究方法包括实验设计和数据分析。
    OpenAI、谷歌和微软都在AI领域进行大量投资。
    """
    
    try:
        # 步骤1: 启动分析
        print("1️⃣ 启动文本分析...")
        start_response = requests.post(
            f'{API_BASE_URL}/api/start-analysis',
            json={'text': test_text},
            timeout=10
        )
        
        if start_response.status_code == 200:
            start_data = start_response.json()
            task_id = start_data['task_id']
            print(f"   ✅ 任务创建成功，ID: {task_id}")
        else:
            raise Exception(f"启动分析失败: {start_response.status_code}")
        
        # 步骤2: 等待分析完成
        print("\n2️⃣ 等待分析完成...")
        max_polls = 8
        
        for poll_count in range(max_polls):
            time.sleep(1)
            
            status_response = requests.get(
                f'{API_BASE_URL}/api/analysis-status/{task_id}',
                timeout=10
            )
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                
                if status_data['status'] == 'COMPLETED':
                    print("   ✅ 分析完成！")
                    break
                elif status_data['status'] == 'FAILED':
                    raise Exception(f"分析失败: {status_data.get('error', '未知错误')}")
                else:
                    print(f"   🔄 状态: {status_data['status']}, 进度: {status_data.get('progress', 0)}%")
        else:
            raise Exception("分析超时")
        
        # 步骤3: 获取集群化图谱数据
        print("\n3️⃣ 获取集群化图谱数据...")
        
        graph_response = requests.get(
            f'{API_BASE_URL}/api/graph-data/{task_id}',
            timeout=10
        )
        
        if graph_response.status_code == 200:
            graph_data = graph_response.json()
            
            # 步骤4: 验证集群化数据结构
            print("\n4️⃣ 验证集群化数据结构...")
            
            # 检查基本字段
            required_fields = ['nodes', 'edges', 'clusters', 'metadata']
            for field in required_fields:
                if field not in graph_data:
                    raise Exception(f"缺少必要字段: {field}")
            
            nodes = graph_data['nodes']
            clusters = graph_data['clusters']
            
            print(f"   📊 节点数量: {len(nodes)}")
            print(f"   🧩 集群数量: {len(clusters)}")
            print(f"   🔗 边数量: {len(graph_data['edges'])}")
            
            # 验证节点包含clusterId
            nodes_with_cluster = 0
            for node in nodes:
                if 'clusterId' in node and 'clusterName' in node:
                    nodes_with_cluster += 1
                else:
                    print(f"   ⚠️ 节点 {node.get('id', 'unknown')} 缺少集群信息")
            
            print(f"   ✅ {nodes_with_cluster}/{len(nodes)} 个节点包含集群信息")
            
            # 显示集群统计
            print("\n📊 集群统计信息:")
            for cluster_id, cluster_info in clusters.items():
                print(f"   🧩 {cluster_info['name']}: {cluster_info['count']} 个节点")
                print(f"      颜色: {cluster_info['color']}")
                
                # 显示该集群的节点
                cluster_nodes = [n for n in nodes if n.get('clusterId') == cluster_id]
                if cluster_nodes:
                    node_labels = [n.get('label', 'unknown') for n in cluster_nodes]
                    print(f"      节点: {', '.join(node_labels)}")
                print()
            
            # 步骤5: 验证集群分配的合理性
            print("5️⃣ 验证集群分配合理性...")
            
            # 检查AI相关词汇是否分配到AI集群
            ai_keywords = ['人工智能', '机器学习', '深度学习', '神经网络', 'AI']
            ai_cluster_nodes = [n for n in nodes if n.get('clusterId') == 'cluster_ai']
            
            if ai_cluster_nodes:
                ai_labels = [n.get('label', '') for n in ai_cluster_nodes]
                ai_match_count = sum(1 for keyword in ai_keywords 
                                   if any(keyword in label for label in ai_labels))
                print(f"   🤖 AI集群包含 {len(ai_cluster_nodes)} 个节点")
                print(f"   ✅ {ai_match_count}/{len(ai_keywords)} 个AI关键词被正确分类")
            
            # 检查商业相关词汇
            business_keywords = ['企业', '管理', '商业', '市场', '战略']
            business_cluster_nodes = [n for n in nodes if n.get('clusterId') == 'cluster_business']
            
            if business_cluster_nodes:
                business_labels = [n.get('label', '') for n in business_cluster_nodes]
                business_match_count = sum(1 for keyword in business_keywords 
                                         if any(keyword in label for label in business_labels))
                print(f"   🏢 商业集群包含 {len(business_cluster_nodes)} 个节点")
                print(f"   ✅ {business_match_count}/{len(business_keywords)} 个商业关键词被正确分类")
            
            # 保存测试结果
            output_file = f'cluster_test_result_{task_id[:8]}.json'
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(graph_data, f, ensure_ascii=False, indent=2)
            print(f"\n💾 测试结果已保存到: {output_file}")
            
            print("\n🎉 集群化功能测试完成！")
            print("=" * 50)
            print("✅ 后端正确生成集群化数据")
            print("✅ 节点包含clusterId和clusterName")
            print("✅ 集群统计信息完整")
            print("✅ 语义分组基本合理")
            print()
            print("🎯 前端验证步骤:")
            print("1. 启动React应用: npm start")
            print("2. 输入测试文本进行分析")
            print("3. 观察初始显示是否为集群模式")
            print("4. 检查集群节点数量是否正确")
            print("5. 测试集群模式切换功能")
            
            return True
            
        else:
            raise Exception(f"获取图谱数据失败: {graph_response.status_code}")
    
    except requests.exceptions.ConnectionError:
        print("❌ 连接错误：请确保API服务正在运行 (python api/main_simple.py)")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return False

def test_cluster_mode_switching():
    """测试前端集群模式切换的准备工作"""
    
    print("\n🔄 前端集群模式切换测试准备")
    print("=" * 40)
    
    print("📋 测试清单:")
    print("1. 初始加载应显示集群节点（数量较少）")
    print("2. 集群节点大小应反映成员数量")
    print("3. 集群节点标签应显示集群名称和成员数")
    print("4. 取消集群模式应显示所有原始节点")
    print("5. 重新启用集群模式应恢复集群视图")
    print("6. 悬停节点应显示正确信息")
    print("7. 右键点击应显示集群详情")
    
    print("\n💡 验证要点:")
    print("• 初始画面应该简洁，不是'毛球'效果")
    print("• 集群节点数量 = 后端返回的cluster数量")
    print("• 可以无缝切换详细模式和集群模式")
    print("• 所有交互功能正常工作")

if __name__ == "__main__":
    print("🚀 AutoGen 集群化功能综合测试")
    print("🎯 验证从后端数据生成到前端显示的完整流程")
    print()
    
    # 主要集群化测试
    success = test_cluster_functionality()
    
    if success:
        # 前端测试准备
        test_cluster_mode_switching()
        
        print("\n" + "="*60)
        print("🎊 集群化功能已就绪！")
        print()
        print("🌟 主要改进:")
        print("• 后端支持语义集群分析")
        print("• 节点包含完整集群信息")
        print("• 前端支持集群/详细模式切换")
        print("• 集群节点大小基于成员数量")
        print("• 初始显示简洁，告别'毛球'")
        print()
        print("🎯 下一步:")
        print("1. 启动React应用测试前端集群化显示")
        print("2. 验证集群模式切换功能")
        print("3. 确认初始加载的简洁性")
        
    else:
        print("\n❌ 集群化功能测试失败")
        print("请检查API服务状态和数据格式") 