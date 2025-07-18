"""
高级推理智能体测试脚本

专门测试高级推理智能体的工作流程，验证其是否严格按照"发现→验证→写入"的顺序执行。
"""

import autogen
import logging
from typing import Dict, Any

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

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def register_reasoning_functions(agent: autogen.AssistantAgent, user_proxy: autogen.UserProxyAgent, graph_db: GraphDB):
    """为智能体注册推理工具函数"""
    
    def find_patterns_wrapper():
        """发现图谱中的有趣模式"""
        logger.info("🔍 执行模式发现...")
        result = find_interesting_patterns(graph_db)
        logger.info(f"📊 发现了 {len(result)} 个潜在模式")
        return result
    
    def verify_hypothesis_wrapper(pattern: Dict[str, Any]):
        """验证模式假设"""
        pattern_type = pattern.get('type', '未知')
        logger.info(f"🧐 验证模式: {pattern_type}")
        result = verify_hypothesis_from_text(pattern, graph_db)
        confidence = result.get('verification', '未知')
        logger.info(f"✅ 验证结果: {confidence}")
        return result
    
    def create_relationship_wrapper(verified_pattern: Dict[str, Any]):
        """创建推理关系"""
        pattern_type = verified_pattern.get('type', '未知')
        confidence = verified_pattern.get('verification', '未知')
        logger.info(f"🔗 创建推理关系: {pattern_type} (置信度: {confidence})")
        result = create_inferred_relationship(verified_pattern, graph_db)
        logger.info(f"💾 创建结果: {result}")
        return result
    
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


def setup_test_data(db: GraphDB):
    """设置测试数据"""
    logger.info("🛠️  设置测试数据...")
    
    # 清理旧数据
    cleanup_query = """
    MATCH (n) WHERE n.name IN [
        '测试张教授', '测试李博士', '测试王研究员', '测试陈学生',
        '测试大学', '测试研究所', '测试AI项目', '测试深度学习论文'
    ] DETACH DELETE n
    """
    db.execute_query(cleanup_query)
    
    # 创建测试节点和关系
    test_data = [
        # 创建人物
        ("CREATE (p:人物 {name: '测试张教授', position: '教授', age: 45})", {}),
        ("CREATE (p:人物 {name: '测试李博士', position: '博士后', age: 32})", {}),
        ("CREATE (p:人物 {name: '测试王研究员', position: '研究员', age: 38})", {}),
        ("CREATE (p:人物 {name: '测试陈学生', position: '博士生', age: 26})", {}),
        
        # 创建机构
        ("CREATE (o:机构 {name: '测试大学', type: '大学'})", {}),
        ("CREATE (o:机构 {name: '测试研究所', type: '研究所'})", {}),
        
        # 创建项目和论文
        ("CREATE (proj:项目 {name: '测试AI项目', budget: 1000000})", {}),
        ("CREATE (paper:论文 {name: '测试深度学习论文', year: 2023})", {}),
        
        # 创建工作关系
        ("""
        MATCH (p:人物 {name: '测试张教授'}), (o:机构 {name: '测试大学'})
        CREATE (p)-[:工作于 {
            source_sentence: '张教授自2010年起在测试大学计算机学院担任教授，主要研究人工智能和机器学习。'
        }]->(o)
        """, {}),
        
        ("""
        MATCH (p:人物 {name: '测试李博士'}), (o:机构 {name: '测试大学'})
        CREATE (p)-[:工作于 {
            source_sentence: '李博士在测试大学进行博士后研究，专注于深度学习算法优化。'
        }]->(o)
        """, {}),
        
        ("""
        MATCH (p:人物 {name: '测试王研究员'}), (o:机构 {name: '测试研究所'})
        CREATE (p)-[:工作于 {
            source_sentence: '王研究员在测试研究所从事人工智能基础理论研究工作。'
        }]->(o)
        """, {}),
        
        # 创建学习关系
        ("""
        MATCH (p:人物 {name: '测试陈学生'}), (o:机构 {name: '测试大学'})
        CREATE (p)-[:就读于 {
            source_sentence: '陈学生在测试大学攻读计算机科学博士学位，师从张教授。'
        }]->(o)
        """, {}),
        
        # 创建项目参与关系
        ("""
        MATCH (p:人物 {name: '测试张教授'}), (proj:项目 {name: '测试AI项目'})
        CREATE (p)-[:参与 {
            source_sentence: '张教授作为项目负责人，领导测试AI项目的研究工作。'
        }]->(proj)
        """, {}),
        
        ("""
        MATCH (p:人物 {name: '测试李博士'}), (proj:项目 {name: '测试AI项目'})
        CREATE (p)-[:参与 {
            source_sentence: '李博士在测试AI项目中负责核心算法的设计和实现。'
        }]->(proj)
        """, {}),
        
        # 创建论文发表关系
        ("""
        MATCH (p:人物 {name: '测试张教授'}), (paper:论文 {name: '测试深度学习论文'})
        CREATE (p)-[:发表 {
            source_sentence: '张教授与团队成员合作发表了关于深度学习的重要论文。'
        }]->(paper)
        """, {}),
        
        ("""
        MATCH (p:人物 {name: '测试陈学生'}), (paper:论文 {name: '测试深度学习论文'})
        CREATE (p)-[:参与 {
            source_sentence: '陈学生作为第二作者参与了深度学习论文的撰写工作。'
        }]->(paper)
        """, {}),
    ]
    
    # 执行所有查询
    for query, params in test_data:
        db.execute_query(query, params)
    
    logger.info("✅ 测试数据设置完成")


def main():
    """主测试函数"""
    logger.info("🧠 高级推理智能体测试开始")
    logger.info("=" * 60)
    
    try:
        # 1. 连接数据库
        logger.info("🔗 连接Neo4j数据库...")
        db = GraphDB(
            uri=config.NEO4J_URI,
            username=config.NEO4J_USERNAME,
            password=config.NEO4J_PASSWORD
        )
        
        if not db.connected:
            logger.error("❌ 数据库连接失败")
            return
        
        logger.info("✅ 数据库连接成功")
        
        # 2. 设置测试数据
        setup_test_data(db)
        
        # 3. 创建推理智能体
        logger.info("\n🤖 创建推理智能体...")
        
        llm_config = config.llm_config_gpt4
        reasoning_agent = create_advanced_reasoning_agent(llm_config)
        reasoning_proxy = create_reasoning_user_proxy()
        
        logger.info("✅ 推理智能体创建成功")
        
        # 4. 注册推理工具函数
        logger.info("\n🔧 注册推理工具函数...")
        register_reasoning_functions(reasoning_agent, reasoning_proxy, db)
        logger.info("✅ 工具函数注册完成")
        
        # 5. 启动推理任务
        logger.info("\n🔍 启动推理分析任务...")
        logger.info("-" * 40)
        
        reasoning_task = "请开始对现有图谱进行深度推理分析，发现并验证隐含的知识关系。严格按照发现→验证→写入的工作流程执行。"
        
        # 开始对话
        reasoning_proxy.initiate_chat(
            reasoning_agent,
            message=reasoning_task,
            max_turns=25  # 允许足够的轮次
        )
        
        # 6. 验证结果
        logger.info("\n📊 验证推理结果...")
        logger.info("-" * 40)
        
        # 查询推理关系
        inferred_query = """
        MATCH (a)-[r]->(b) 
        WHERE r.type = 'INFERRED'
        RETURN a.name as source, type(r) as rel_type, b.name as target, 
               r.confidence as confidence, r.pattern_type as pattern_type
        ORDER BY r.confidence DESC
        """
        
        inferred_relations = db.execute_query(inferred_query)
        
        if inferred_relations:
            logger.info(f"🎉 智能体成功创建了 {len(inferred_relations)} 个推理关系:")
            for i, rel in enumerate(inferred_relations, 1):
                logger.info(f"   {i}. {rel['source']} --[{rel['rel_type']}]--> {rel['target']}")
                logger.info(f"      置信度: {rel['confidence']}, 模式: {rel['pattern_type']}")
        else:
            logger.info("⚠️  未发现新的推理关系")
        
        # 7. 清理测试数据
        logger.info("\n🧹 清理测试数据...")
        
        # 清理测试节点
        cleanup_query = """
        MATCH (n) WHERE n.name CONTAINS '测试'
        DETACH DELETE n
        """
        db.execute_query(cleanup_query)
        
        # 清理推理关系
        cleanup_inferred = "MATCH ()-[r]->() WHERE r.type = 'INFERRED' DELETE r"
        db.execute_query(cleanup_inferred)
        
        logger.info("✅ 测试数据清理完成")
        
        logger.info("\n🎯 高级推理智能体测试完成！")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if 'db' in locals() and hasattr(db, 'close'):
            db.close()


if __name__ == "__main__":
    main() 