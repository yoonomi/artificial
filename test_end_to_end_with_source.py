#!/usr/bin/env python3
"""
端到端溯源信息测试脚本

测试完整的知识图谱构建流程，包括溯源信息的处理和存储
"""

import json
import sys
from config import config
from agents.ece_agent import create_ece_agent
from agents.ree_agent import create_ree_agent
from agents.graph_synthesis_agent import create_graph_synthesis_agent
from tools.graph_db import GraphDB
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_complete_pipeline():
    """测试完整的知识图谱构建管道"""
    print("🎯 开始端到端溯源信息测试...")
    print("=" * 80)
    
    # 测试文本
    test_text = """
    阿兰·图灵是英国数学家和计算机科学家，被誉为计算机科学之父。
    他在1950年提出了著名的图灵测试来判断机器智能。
    约翰·麦卡锡在1956年的达特茅斯会议上正式提出了"人工智能"这个术语。
    DeepMind开发的AlphaGo在2016年击败了世界围棋冠军李世石。
    """
    
    print(f"📝 测试文本：{test_text.strip()}")
    
    # 本体论定义
    ontology_json = """
    {
        "node_labels": ["人物", "机构", "技术", "时间", "事件", "概念"],
        "relationship_types": ["提出", "发明", "开发", "击败", "发生于", "工作于", "参与"]
    }
    """
    
    # Step 1: 实体抽取
    print("\n🔍 Step 1: 实体抽取...")
    ece_agent = create_ece_agent(config.llm_config_gpt4, ontology_json)
    
    try:
        ece_response = ece_agent.generate_reply(
            messages=[{"role": "user", "content": test_text}]
        )
        
        # 解析实体结果
        entities = parse_json_response(ece_response)
        print(f"✅ 成功提取 {len(entities)} 个实体")
        
        for entity in entities[:3]:  # 显示前3个实体
            print(f"  - {entity['text']} ({entity['label']}) - 溯源: {entity['source_sentence'][:50]}...")
            
    except Exception as e:
        print(f"❌ 实体抽取失败: {e}")
        return False
    
    # Step 2: 关系抽取
    print("\n🔍 Step 2: 关系抽取...")
    entities_json = json.dumps(entities, ensure_ascii=False)
    relationship_types = ["提出", "发明", "开发", "击败", "发生于", "工作于", "参与"]
    
    ree_agent = create_ree_agent(config.llm_config_gpt4, entities_json, relationship_types)
    
    try:
        ree_response = ree_agent.generate_reply(
            messages=[{"role": "user", "content": test_text}]
        )
        
        # 解析关系结果
        relations = parse_json_response(ree_response)
        print(f"✅ 成功提取 {len(relations)} 个关系")
        
        for relation in relations[:3]:  # 显示前3个关系
            print(f"  - {relation['source_entity_id']} → {relation['target_entity_id']} ({relation['relationship_type']})")
            print(f"    溯源: {relation['source_sentence'][:50]}...")
            
    except Exception as e:
        print(f"❌ 关系抽取失败: {e}")
        return False
    
    # Step 3: 图谱合成和Cypher生成
    print("\n🔍 Step 3: 图谱合成和Cypher生成...")
    graph_agent = create_graph_synthesis_agent(config.llm_config_gpt4)
    
    # 构建输入数据
    graph_input = {
        "entities": entities,
        "relations": relations
    }
    
    graph_input_text = f"""
    请根据以下实体和关系数据生成Neo4j Cypher查询语句：

    实体数据：
    {json.dumps(entities, ensure_ascii=False, indent=2)}

    关系数据：
    {json.dumps(relations, ensure_ascii=False, indent=2)}
    """
    
    try:
        graph_response = graph_agent.generate_reply(
            messages=[{"role": "user", "content": graph_input_text}]
        )
        
        # 解析Cypher查询
        cypher_data = parse_json_response(graph_response)
        cypher_statements = cypher_data.get('cypher_statements', [])
        
        print(f"✅ 成功生成 {len(cypher_statements)} 条Cypher语句")
        
        for i, statement in enumerate(cypher_statements[:3]):  # 显示前3条语句
            print(f"  {i+1}. {statement[:80]}...")
            
    except Exception as e:
        print(f"❌ 图谱合成失败: {e}")
        return False
    
    # Step 4: 数据库执行
    print("\n🔍 Step 4: 执行Cypher语句并存储到Neo4j...")
    
    try:
        # 连接数据库
        db = GraphDB(
            uri=config.NEO4J_URI,
            username=config.NEO4J_USERNAME,
            password=config.NEO4J_PASSWORD
        )
        
        if not db.connected:
            print("❌ 数据库连接失败")
            return False
        
        print("✅ 数据库连接成功")
        
        # 清理旧的测试数据
        cleanup_query = """
        MATCH (n) WHERE n.unique_id STARTS WITH 'entity_' OR n.name IN ['阿兰·图灵', '约翰·麦卡锡', 'AlphaGo', 'DeepMind', '李世石']
        DETACH DELETE n
        """
        db.execute_query(cleanup_query)
        print("✅ 清理旧数据完成")
        
        # 执行Cypher语句
        executed_count = 0
        for statement in cypher_statements:
            try:
                result = db.execute_query(statement)
                executed_count += 1
                logger.info(f"执行成功: {statement[:50]}...")
            except Exception as e:
                logger.error(f"执行失败: {statement[:50]}... 错误: {e}")
        
        print(f"✅ 成功执行 {executed_count}/{len(cypher_statements)} 条语句")
        
    except Exception as e:
        print(f"❌ 数据库操作失败: {e}")
        return False
    
    # Step 5: 验证溯源信息存储
    print("\n🔍 Step 5: 验证溯源信息存储...")
    
    try:
        # 检查节点的溯源信息
        node_query = """
        MATCH (n) WHERE n.source_sentence IS NOT NULL
        RETURN n.name as name, labels(n)[0] as label, n.source_sentence as source_sentence
        LIMIT 10
        """
        
        node_results = db.execute_query(node_query)
        print(f"✅ 找到 {len(node_results)} 个包含溯源信息的节点:")
        
        for result in node_results[:5]:  # 显示前5个
            print(f"  - {result['name']} ({result['label']})")
            print(f"    溯源: {result['source_sentence'][:60]}...")
        
        # 检查关系的溯源信息
        rel_query = """
        MATCH ()-[r]->() WHERE r.source_sentence IS NOT NULL
        RETURN type(r) as rel_type, r.source_sentence as source_sentence
        LIMIT 10
        """
        
        rel_results = db.execute_query(rel_query)
        print(f"✅ 找到 {len(rel_results)} 个包含溯源信息的关系:")
        
        for result in rel_results[:5]:  # 显示前5个
            print(f"  - {result['rel_type']}")
            print(f"    溯源: {result['source_sentence'][:60]}...")
            
        # 验证成功条件
        if len(node_results) > 0 and len(rel_results) > 0:
            print("\n🎉 溯源信息验证成功！")
            print("✅ 节点和关系都包含有效的溯源信息")
            return True
        else:
            print("\n❌ 溯源信息验证失败：未找到包含溯源信息的节点或关系")
            return False
            
    except Exception as e:
        print(f"❌ 溯源信息验证失败: {e}")
        return False


def parse_json_response(response):
    """解析AI响应中的JSON内容"""
    json_text = response.strip()
    
    # 处理markdown代码块
    if json_text.startswith("```json"):
        json_text = json_text[7:]
        if json_text.endswith("```"):
            json_text = json_text[:-3]
    elif json_text.startswith("```"):
        json_text = json_text[3:]
        if json_text.endswith("```"):
            json_text = json_text[:-3]
    
    json_text = json_text.strip()
    return json.loads(json_text)


def show_neo4j_queries():
    """显示用于验证的Neo4j查询语句"""
    print("\n📊 Neo4j验证查询:")
    print("=" * 50)
    
    print("1. 检查包含溯源信息的节点：")
    print("```cypher")
    print("MATCH (n) WHERE n.source_sentence IS NOT NULL")
    print("RETURN n.name, n.source_sentence")
    print("LIMIT 10")
    print("```")
    
    print("\n2. 检查包含溯源信息的关系：")
    print("```cypher")
    print("MATCH ()-[r]->() WHERE r.source_sentence IS NOT NULL")
    print("RETURN type(r), r.source_sentence")
    print("LIMIT 10")
    print("```")
    
    print("\n3. 查看完整的知识图谱：")
    print("```cypher")
    print("MATCH (n)-[r]->(m)")
    print("RETURN n.name, type(r), m.name, r.source_sentence")
    print("LIMIT 20")
    print("```")


def main():
    """主函数"""
    try:
        success = test_complete_pipeline()
        
        print("\n" + "=" * 80)
        if success:
            print("🎉 端到端溯源信息测试完全成功！")
            print("✅ 所有组件正常工作，溯源信息已正确存储到数据库")
        else:
            print("❌ 端到端测试失败，请检查上述错误信息")
        
        show_neo4j_queries()
        
        return 0 if success else 1
        
    except Exception as e:
        print(f"❌ 测试过程中发生意外错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main()) 