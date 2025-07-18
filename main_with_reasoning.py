"""
AutoGen知识图谱生成系统 - 含高级推理功能

这个版本包含完整的知识图谱生成流程，以及高级推理智能体的集成。
工作流程：文本分析 -> 实体提取 -> 图谱构建 -> 深度推理分析
"""

import autogen
import logging
import sys
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

# 导入配置和工具
from config import config
from tools.graph_db import GraphDB
from tools.reasoning_tools import (
    find_interesting_patterns,
    verify_hypothesis_from_text,
    create_inferred_relationship
)
from agents.advanced_reasoning_agent import (
    create_advanced_reasoning_agent,
    create_reasoning_user_proxy
)

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout
)
logger = logging.getLogger(__name__)


def create_simplified_ontologist_agent(llm_config: Dict) -> autogen.AssistantAgent:
    """创建简化的本体论专家智能体"""
    
    system_message = """你是一位本体论专家。请分析文本并设计知识图谱架构。

输出要求：
必须返回严格的JSON格式，包含两个字段：
{
  "node_labels": ["实体类型1", "实体类型2", ...],
  "relationship_types": ["关系类型1", "关系类型2", ...]
}

不要添加任何解释文字，只返回JSON。"""

    return autogen.AssistantAgent(
        name="SimplifiedOntologist",
        system_message=system_message,
        llm_config=llm_config,
        max_consecutive_auto_reply=1,
    )


def create_entity_extraction_agent(llm_config: Dict) -> autogen.AssistantAgent:
    """创建实体提取智能体"""
    
    system_message = """你是一位实体提取专家。请从文本中提取实体和关系。

输出要求：
必须返回严格的JSON格式：
{
  "entities": [
    {"name": "实体名", "type": "实体类型", "properties": {"属性": "值"}},
    ...
  ],
  "relationships": [
    {"source": "源实体名", "target": "目标实体名", "type": "关系类型", "properties": {"source_sentence": "支持该关系的原文句子"}},
    ...
  ]
}

重要：每个关系必须包含source_sentence属性，用于后续推理分析。
不要添加任何解释文字，只返回JSON。"""

    return autogen.AssistantAgent(
        name="EntityExtractor", 
        system_message=system_message,
        llm_config=llm_config,
        max_consecutive_auto_reply=1,
    )


def register_reasoning_functions(agent: autogen.AssistantAgent, user_proxy: autogen.UserProxyAgent, graph_db: GraphDB):
    """
    为智能体注册推理工具函数
    
    Args:
        agent: 要注册函数的智能体
        user_proxy: 用户代理
        graph_db: 图数据库实例
    """
    
    # 创建包装函数，以便传递graph_db参数
    def find_patterns_wrapper():
        """发现图谱中的有趣模式"""
        return find_interesting_patterns(graph_db)
    
    def verify_hypothesis_wrapper(pattern: Dict[str, Any]):
        """验证模式假设"""
        return verify_hypothesis_from_text(pattern, graph_db)
    
    def create_relationship_wrapper(verified_pattern: Dict[str, Any]):
        """创建推理关系"""
        return create_inferred_relationship(verified_pattern, graph_db)
    
    # 注册函数到智能体
    autogen.register_function(
        find_patterns_wrapper,
        caller=agent,
        executor=user_proxy,
        name="find_interesting_patterns",
        description="在知识图谱中发现潜在的有趣模式，用于推理分析"
    )
    
    autogen.register_function(
        verify_hypothesis_wrapper,
        caller=agent,
        executor=user_proxy,
        name="verify_hypothesis_from_text",
        description="验证发现的模式是否构成有意义的隐含关系"
    )
    
    autogen.register_function(
        create_relationship_wrapper,
        caller=agent,
        executor=user_proxy,
        name="create_inferred_relationship",
        description="将验证为高置信度的隐含关系写入图谱"
    )


def extract_json_from_response(response_content: str) -> Optional[Dict]:
    """从响应中提取JSON内容"""
    try:
        # 直接尝试解析
        return json.loads(response_content.strip())
    except json.JSONDecodeError:
        try:
            # 尝试提取代码块中的JSON
            if '```json' in response_content:
                start_marker = '```json'
                end_marker = '```'
                start_idx = response_content.find(start_marker) + len(start_marker)
                end_idx = response_content.find(end_marker, start_idx)
                if end_idx != -1:
                    json_content = response_content[start_idx:end_idx].strip()
                    return json.loads(json_content)
            elif '```' in response_content:
                parts = response_content.split('```')
                if len(parts) >= 3:
                    json_content = parts[1].strip()
                    return json.loads(json_content)
            
            # 尝试查找JSON对象
            start_idx = response_content.find('{')
            end_idx = response_content.rfind('}') + 1
            if start_idx != -1 and end_idx > start_idx:
                json_str = response_content[start_idx:end_idx]
                return json.loads(json_str)
                
        except json.JSONDecodeError:
            pass
    
    return None


def save_to_graph_db(ontology: Dict, entities_and_relations: Dict, graph_db: GraphDB) -> bool:
    """将提取的数据保存到图数据库"""
    try:
        logger.info("开始保存数据到图数据库...")
        
        # 导入实体
        entities = entities_and_relations.get('entities', [])
        logger.info(f"准备导入 {len(entities)} 个实体")
        
        for entity in entities:
            success = graph_db.import_entity(entity)
            if success:
                logger.info(f"成功导入实体: {entity['name']}")
            else:
                logger.warning(f"导入实体失败: {entity['name']}")
        
        # 导入关系
        relationships = entities_and_relations.get('relationships', [])
        logger.info(f"准备导入 {len(relationships)} 个关系")
        
        for relationship in relationships:
            success = graph_db.import_relationship(relationship)
            if success:
                logger.info(f"成功导入关系: {relationship['source']} -> {relationship['target']}")
            else:
                logger.warning(f"导入关系失败: {relationship['source']} -> {relationship['target']}")
        
        logger.info("数据导入完成")
        return True
        
    except Exception as e:
        logger.error(f"保存到图数据库时出错: {e}")
        return False


def main():
    """主函数 - 完整的知识图谱生成和推理流程"""
    logger.info("🚀 AutoGen知识图谱生成系统启动 (含高级推理功能)")
    
    try:
        # 1. 初始化数据库连接
        logger.info("📊 初始化数据库连接...")
        graph_db = GraphDB(
            uri=config.NEO4J_URI,
            username=config.NEO4J_USERNAME,
            password=config.NEO4J_PASSWORD
        )
        
        if not graph_db.connected:
            logger.error("❌ 数据库连接失败")
            return
        
        logger.info("✅ 数据库连接成功")
        
        # 2. 读取测试文本
        logger.info("📖 读取测试文本...")
        text_file = Path("data/sample_text.txt")
        
        if not text_file.exists():
            logger.error(f"❌ 文本文件未找到: {text_file}")
            return
        
        with open(text_file, 'r', encoding='utf-8') as f:
            sample_text = f.read().strip()
        
        logger.info(f"✅ 成功读取文本 ({len(sample_text)} 字符)")
        
        # 3. 创建基础智能体
        logger.info("🤖 创建基础智能体...")
        
        llm_config = config.llm_config_gpt4
        
        ontologist = create_simplified_ontologist_agent(llm_config)
        extractor = create_entity_extraction_agent(llm_config)
        
        user_proxy = autogen.UserProxyAgent(
            name="UserProxy",
            code_execution_config=False,
            human_input_mode="NEVER",
            max_consecutive_auto_reply=0,
        )
        
        logger.info("✅ 基础智能体创建完成")
        
        # 4. 第一阶段：本体设计
        logger.info("\n🧠 第一阶段：本体设计")
        logger.info("=" * 50)
        
        ontology_task = f"请为以下文本设计知识图谱架构：\n\n{sample_text}"
        
        user_proxy.initiate_chat(ontologist, message=ontology_task, max_turns=1)
        ontology_response = user_proxy.last_message(agent=ontologist)["content"]
        
        logger.info(f"本体论专家响应: {ontology_response}")
        
        ontology_data = extract_json_from_response(ontology_response)
        if not ontology_data:
            logger.error("❌ 无法解析本体设计响应")
            return
        
        logger.info(f"✅ 本体设计完成: {len(ontology_data.get('node_labels', []))} 个实体类型, {len(ontology_data.get('relationship_types', []))} 个关系类型")
        
        # 5. 第二阶段：实体和关系提取  
        logger.info("\n🔍 第二阶段：实体和关系提取")
        logger.info("=" * 50)
        
        extraction_task = f"""请从以下文本中提取实体和关系，遵循设计的本体架构：

本体架构：
- 实体类型: {', '.join(ontology_data.get('node_labels', []))}
- 关系类型: {', '.join(ontology_data.get('relationship_types', []))}

文本内容：
{sample_text}"""
        
        user_proxy.initiate_chat(extractor, message=extraction_task, max_turns=1)
        extraction_response = user_proxy.last_message(agent=extractor)["content"]
        
        logger.info(f"实体提取专家响应: {extraction_response}")
        
        entities_data = extract_json_from_response(extraction_response)
        if not entities_data:
            logger.error("❌ 无法解析实体提取响应")
            return
        
        entities_count = len(entities_data.get('entities', []))
        relations_count = len(entities_data.get('relationships', []))
        logger.info(f"✅ 实体提取完成: {entities_count} 个实体, {relations_count} 个关系")
        
        # 6. 第三阶段：保存到图数据库
        logger.info("\n💾 第三阶段：保存到图数据库")
        logger.info("=" * 50)
        
        success = save_to_graph_db(ontology_data, entities_data, graph_db)
        if not success:
            logger.error("❌ 保存到图数据库失败")
            return
        
        logger.info("✅ 基础图谱构建完成")
        
        # 7. 第四阶段：高级推理分析
        logger.info("\n🧠 第四阶段：高级推理分析")
        logger.info("=" * 60)
        
        # 创建推理智能体
        reasoning_agent = create_advanced_reasoning_agent(llm_config)
        reasoning_proxy = create_reasoning_user_proxy()
        
        # 注册推理工具函数
        logger.info("🔧 注册推理工具函数...")
        register_reasoning_functions(reasoning_agent, reasoning_proxy, graph_db)
        logger.info("✅ 推理工具函数注册完成")
        
        # 启动推理分析
        logger.info("🔍 启动深度推理分析...")
        
        reasoning_task = "请开始对现有图谱进行深度推理分析，发现并验证隐含的知识关系。"
        
        # 开始推理对话
        reasoning_proxy.initiate_chat(
            reasoning_agent, 
            message=reasoning_task,
            max_turns=20  # 允许足够的轮次完成推理
        )
        
        # 8. 查看最终结果
        logger.info("\n📊 第五阶段：结果验证")
        logger.info("=" * 50)
        
        # 查询推理关系
        inferred_query = """
        MATCH (a)-[r]->(b) 
        WHERE r.type = 'INFERRED'
        RETURN a.name as source, type(r) as rel_type, b.name as target, r.confidence as confidence
        ORDER BY r.confidence DESC
        """
        
        inferred_relations = graph_db.execute_query(inferred_query)
        
        if inferred_relations:
            logger.info(f"🎉 成功创建了 {len(inferred_relations)} 个推理关系:")
            for rel in inferred_relations:
                logger.info(f"   {rel['source']} --[{rel['rel_type']}]--> {rel['target']} (置信度: {rel['confidence']})")
        else:
            logger.info("⚠️  未发现新的推理关系")
        
        # 查询总体图谱统计
        stats_query = """
        MATCH (n) 
        WITH labels(n) as node_labels
        UNWIND node_labels as label
        RETURN label, count(*) as count
        ORDER BY count DESC
        """
        
        node_stats = graph_db.execute_query(stats_query)
        
        logger.info("\n📈 最终图谱统计:")
        total_nodes = 0
        for stat in node_stats:
            count = stat['count']
            total_nodes += count
            logger.info(f"   {stat['label']}: {count} 个节点")
        
        rel_stats_query = """
        MATCH ()-[r]->() 
        RETURN type(r) as rel_type, count(r) as count
        ORDER BY count DESC
        """
        
        rel_stats = graph_db.execute_query(rel_stats_query)
        
        total_rels = 0
        for stat in rel_stats:
            count = stat['count']
            total_rels += count
            logger.info(f"   {stat['rel_type']}: {count} 个关系")
        
        logger.info(f"\n🎯 系统完成！总计: {total_nodes} 个节点, {total_rels} 个关系")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ 系统执行出错: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if 'graph_db' in locals() and hasattr(graph_db, 'close'):
            graph_db.close()


if __name__ == "__main__":
    main() 