"""
手动测试知识图谱导入

使用我们成功抽取的部分数据，手动完成数据库导入测试，
验证整个端到端流程的可行性。
"""

import json
import logging
import sys
from config import config
from tools.graph_db import GraphDB

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout
)
logger = logging.getLogger(__name__)


def create_sample_knowledge_graph():
    """创建示例知识图谱数据"""
    return {
        "nodes": [
            {
                "id": "N001",
                "label": "人工智能技术",
                "type": "人工智能技术",
                "properties": {
                    "name": "人工智能",
                    "description": "计算机科学的一个重要分支"
                }
            },
            {
                "id": "N002", 
                "label": "阿兰·图灵",
                "type": "人物",
                "properties": {
                    "name": "阿兰·图灵",
                    "description": "英国数学家"
                }
            },
            {
                "id": "N003",
                "label": "计算机器与智能",
                "type": "论文",
                "properties": {
                    "name": "计算机器与智能",
                    "description": "著名的论文"
                }
            },
            {
                "id": "N004",
                "label": "图灵测试",
                "type": "概念",
                "properties": {
                    "name": "图灵测试",
                    "description": "人工智能研究的开端"
                }
            },
            {
                "id": "N005",
                "label": "约翰·麦卡锡",
                "type": "人物",
                "properties": {
                    "name": "约翰·麦卡锡",
                    "description": "首次提出了人工智能术语"
                }
            },
            {
                "id": "N006",
                "label": "达特茅斯学院",
                "type": "机构",
                "properties": {
                    "name": "达特茅斯学院",
                    "description": "美国大学"
                }
            },
            {
                "id": "N007",
                "label": "AlphaGo",
                "type": "系统", 
                "properties": {
                    "name": "AlphaGo",
                    "description": "谷歌DeepMind开发的围棋AI"
                }
            },
            {
                "id": "N008",
                "label": "李世石",
                "type": "人物",
                "properties": {
                    "name": "李世石", 
                    "description": "围棋世界冠军"
                }
            },
            {
                "id": "N009",
                "label": "谷歌DeepMind",
                "type": "机构",
                "properties": {
                    "name": "谷歌DeepMind",
                    "description": "AI研究公司"
                }
            },
            {
                "id": "N010",
                "label": "OpenAI",
                "type": "机构",
                "properties": {
                    "name": "OpenAI",
                    "description": "AI研究机构"
                }
            },
            {
                "id": "N011",
                "label": "GPT",
                "type": "模型",
                "properties": {
                    "name": "GPT",
                    "description": "生成式预训练变换器"
                }
            }
        ],
        "edges": [
            {
                "id": "E001",
                "source": "N002",
                "target": "N003", 
                "type": "发表",
                "properties": {"confidence": 0.9, "year": "1950"}
            },
            {
                "id": "E002",
                "source": "N002",
                "target": "N004",
                "type": "提出",
                "properties": {"confidence": 0.95, "year": "1950"}
            },
            {
                "id": "E003",
                "source": "N005",
                "target": "N001",
                "type": "提出",
                "properties": {"confidence": 0.9, "year": "1956"}
            },
            {
                "id": "E004",
                "source": "N005",
                "target": "N006",
                "type": "参与",
                "properties": {"confidence": 0.8, "year": "1956"}
            },
            {
                "id": "E005",
                "source": "N007",
                "target": "N008", 
                "type": "击败",
                "properties": {"confidence": 1.0, "year": "2016"}
            },
            {
                "id": "E006",
                "source": "N009",
                "target": "N007",
                "type": "开发",
                "properties": {"confidence": 1.0}
            },
            {
                "id": "E007",
                "source": "N010",
                "target": "N011",
                "type": "发布",
                "properties": {"confidence": 1.0, "year": "2018"}
            },
            {
                "id": "E008",
                "source": "N004",
                "target": "N001",
                "type": "标志着",
                "properties": {"confidence": 0.9, "relationship": "开端"}
            }
        ],
        "metadata": {
            "node_count": 11,
            "edge_count": 8,
            "creation_time": "2025-07-18T10:59:00Z",
            "source": "AutoGen AI System",
            "version": "1.0"
        }
    }


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("🧠 手动测试知识图谱导入")
    logger.info("=" * 60)
    
    try:
        # 创建示例知识图谱
        knowledge_graph = create_sample_knowledge_graph()
        
        logger.info(f"📊 准备导入知识图谱:")
        logger.info(f"   📈 节点数: {len(knowledge_graph['nodes'])}")
        logger.info(f"   🔗 边数: {len(knowledge_graph['edges'])}")
        
        # 初始化数据库连接
        graph_db = GraphDB(
            uri=config.NEO4J_URI,
            username=config.NEO4J_USERNAME,
            password=config.NEO4J_PASSWORD
        )
        
        if not graph_db.connected:
            logger.error("❌ 无法连接到Neo4j数据库")
            return
        
        logger.info("✅ Neo4j数据库连接成功")
        
        # 导入知识图谱
        logger.info("🔄 开始导入知识图谱...")
        success = graph_db.import_knowledge_graph(knowledge_graph)
        
        if success:
            logger.info("🎉 知识图谱导入成功!")
            logger.info("=" * 60)
            logger.info("📋 导入摘要:")
            logger.info(f"   👥 人物: 阿兰·图灵, 约翰·麦卡锡, 李世石")
            logger.info(f"   🏢 机构: 达特茅斯学院, 谷歌DeepMind, OpenAI")
            logger.info(f"   🤖 系统: AlphaGo, GPT")
            logger.info(f"   📝 论文: 计算机器与智能")
            logger.info(f"   💡 概念: 图灵测试, 人工智能技术")
            logger.info("=" * 60)
            logger.info("💡 请打开Neo4j Browser查看结果:")
            logger.info("🌐 网址: http://localhost:7474")
            logger.info("🔍 查询: MATCH (n) RETURN n LIMIT 25")
            logger.info("🔍 查看人物: MATCH (n:人物) RETURN n")
            logger.info("🔍 查看关系: MATCH (a)-[r]->(b) RETURN a.name, type(r), b.name")
        else:
            logger.error("❌ 知识图谱导入失败")
        
        # 断开连接
        graph_db.disconnect()
        
    except Exception as e:
        logger.error(f"💥 执行失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 