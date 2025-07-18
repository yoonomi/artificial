"""
AutoGen知识图谱生成系统 - 简化版本

这是一个简化的版本，使用更少的智能体和更直接的工作流，
专门用于测试和演示核心功能。
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


def create_simplified_extractor_agent(llm_config: Dict) -> autogen.AssistantAgent:
    """创建简化的实体抽取智能体"""
    
    system_message = """你是实体抽取专家。根据提供的本体架构，从文本中抽取实体和关系。

输出要求：
必须返回严格的JSON格式：
{
  "nodes": [
    {
      "id": "N001",
      "label": "节点名称", 
      "type": "节点类型",
      "properties": {"name": "名称", "description": "描述"}
    }
  ],
  "edges": [
    {
      "id": "E001",
      "source": "N001",
      "target": "N002", 
      "type": "关系类型",
      "properties": {"confidence": 0.9}
    }
  ]
}

不要添加任何解释文字，只返回JSON。"""

    return autogen.AssistantAgent(
        name="SimplifiedExtractor",
        system_message=system_message,
        llm_config=llm_config,
        max_consecutive_auto_reply=1,
    )


class SimplifiedWorkflow:
    """简化的知识图谱生成工作流"""
    
    def __init__(self):
        self.config = config
        self.llm_config = self.config.llm_config_gpt4
        self.graph_db = None
        
        # 初始化数据库连接
        self._init_database()
        
    def _init_database(self):
        """初始化数据库连接"""
        try:
            self.graph_db = GraphDB(
                uri=self.config.NEO4J_URI,
                username=self.config.NEO4J_USERNAME,
                password=self.config.NEO4J_PASSWORD
            )
            if self.graph_db.connected:
                logger.info("✅ Neo4j数据库连接成功")
            else:
                logger.warning("⚠️ Neo4j数据库连接失败，将跳过数据库保存")
        except Exception as e:
            logger.error(f"❌ 数据库初始化失败: {e}")
            self.graph_db = None
    
    def load_sample_text(self, file_path: str = "data/sample_text.txt") -> str:
        """加载示例文本（截取前500字符以减少处理时间）"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read().strip()
            
            # 截取前800字符以减少处理时间和网络请求大小
            if len(text) > 800:
                text = text[:800] + "..."
                
            logger.info(f"📖 成功加载文本文件: {file_path} ({len(text)} 字符)")
            return text
        except Exception as e:
            logger.error(f"❌ 加载文本文件失败: {e}")
            return """
人工智能技术发展历程

1950年，阿兰·图灵提出了图灵测试。
1956年，约翰·麦卡锡在达特茅斯会议上首次提出"人工智能"概念。
2016年，谷歌的AlphaGo击败了围棋世界冠军李世石。
2022年，OpenAI发布了ChatGPT，引发了新一轮AI热潮。
            """.strip()
    
    def step1_design_ontology(self, text: str) -> Dict:
        """步骤1：设计本体架构"""
        logger.info("🔍 步骤1: 设计本体架构...")
        
        try:
            ontologist = create_simplified_ontologist_agent(self.llm_config)
            user_proxy = autogen.UserProxyAgent(
                name="UserProxy",
                human_input_mode="NEVER",
                max_consecutive_auto_reply=0,
                code_execution_config=False,
            )
            
            message = f"请分析以下文本并设计本体架构：\n\n{text}"
            
            # 启动对话
            user_proxy.initiate_chat(ontologist, message=message, max_turns=1)
            
            # 获取结果
            last_message = user_proxy.last_message()["content"]
            logger.info(f"📋 本体设计结果: {last_message}")
            
            # 解析JSON
            try:
                start_idx = last_message.find('{')
                end_idx = last_message.rfind('}') + 1
                
                if start_idx != -1 and end_idx > start_idx:
                    json_str = last_message[start_idx:end_idx]
                    ontology = json.loads(json_str)
                    logger.info("✅ 本体架构设计成功")
                    return ontology
                else:
                    logger.error("❌ 未找到有效的JSON格式")
                    return None
                    
            except json.JSONDecodeError as e:
                logger.error(f"❌ JSON解析失败: {e}")
                return None
                
        except Exception as e:
            logger.error(f"❌ 本体设计失败: {e}")
            return None
    
    def step2_extract_knowledge(self, text: str, ontology: Dict) -> Dict:
        """步骤2：抽取知识图谱"""
        logger.info("🔍 步骤2: 抽取知识图谱...")
        
        try:
            # 添加延迟以避免请求过于频繁
            time.sleep(3)
            
            extractor = create_simplified_extractor_agent(self.llm_config)
            user_proxy = autogen.UserProxyAgent(
                name="UserProxy",
                human_input_mode="NEVER",
                max_consecutive_auto_reply=0,
                code_execution_config=False,
            )
            
            message = f"""
根据以下本体架构从文本中抽取知识图谱：

本体架构：
{json.dumps(ontology, ensure_ascii=False, indent=2)}

文本内容：
{text}

请抽取实体和关系构建知识图谱。
"""
            
            # 启动对话
            user_proxy.initiate_chat(extractor, message=message, max_turns=1)
            
            # 获取结果
            last_message = user_proxy.last_message()["content"]
            logger.info(f"📋 知识抽取结果: {last_message}")
            
            # 解析JSON
            try:
                start_idx = last_message.find('{')
                end_idx = last_message.rfind('}') + 1
                
                if start_idx != -1 and end_idx > start_idx:
                    json_str = last_message[start_idx:end_idx]
                    knowledge_graph = json.loads(json_str)
                    logger.info("✅ 知识图谱抽取成功")
                    return knowledge_graph
                else:
                    logger.error("❌ 未找到有效的JSON格式")
                    return None
                    
            except json.JSONDecodeError as e:
                logger.error(f"❌ JSON解析失败: {e}")
                return None
                
        except Exception as e:
            logger.error(f"❌ 知识抽取失败: {e}")
            return None
    
    def step3_save_to_database(self, knowledge_graph: Dict) -> bool:
        """步骤3：保存到数据库"""
        logger.info("🔍 步骤3: 保存到数据库...")
        
        if not self.graph_db or not self.graph_db.connected:
            logger.warning("⚠️ 数据库未连接，跳过保存")
            return False
        
        try:
            success = self.graph_db.import_knowledge_graph(knowledge_graph)
            if success:
                logger.info("✅ 知识图谱已成功保存到Neo4j数据库")
            else:
                logger.error("❌ 知识图谱保存失败")
            return success
        except Exception as e:
            logger.error(f"❌ 保存到数据库时出错: {e}")
            return False
    
    def run_simplified_workflow(self, input_text: str):
        """运行简化的工作流"""
        logger.info("🚀 开始简化知识图谱生成工作流...")
        
        try:
            # 步骤1：设计本体架构
            ontology = self.step1_design_ontology(input_text)
            if not ontology:
                logger.error("❌ 本体设计失败，工作流中止")
                return
            
            # 步骤2：抽取知识图谱
            knowledge_graph = self.step2_extract_knowledge(input_text, ontology)
            if not knowledge_graph:
                logger.error("❌ 知识抽取失败，工作流中止")
                return
            
            # 步骤3：保存到数据库
            self.step3_save_to_database(knowledge_graph)
            
            # 输出结果摘要
            self.print_summary(ontology, knowledge_graph)
            
            logger.info("✅ 简化工作流执行完成")
            
        except Exception as e:
            logger.error(f"❌ 工作流执行失败: {e}")
            raise
    
    def print_summary(self, ontology: Dict, knowledge_graph: Dict):
        """打印执行摘要"""
        logger.info("\n" + "=" * 60)
        logger.info("📊 知识图谱生成摘要")
        logger.info("=" * 60)
        
        if ontology:
            logger.info(f"🏗️ 实体类型数量: {len(ontology.get('node_labels', []))}")
            logger.info(f"🔗 关系类型数量: {len(ontology.get('relationship_types', []))}")
        
        if knowledge_graph:
            logger.info(f"📈 生成节点数: {len(knowledge_graph.get('nodes', []))}")
            logger.info(f"🔗 生成边数: {len(knowledge_graph.get('edges', []))}")
        
        logger.info("=" * 60)


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("🧠 AutoGen知识图谱生成系统启动（简化版）")
    logger.info("=" * 60)
    
    try:
        # 检查API密钥配置
        if not config.OPENAI_API_KEY or config.OPENAI_API_KEY == "your_openai_api_key_here":
            logger.error("❌ OpenAI API密钥未配置，请检查.env文件")
            return
        
        # 创建简化工作流管理器
        workflow = SimplifiedWorkflow()
        
        # 加载示例文本
        sample_text = workflow.load_sample_text()
        
        logger.info(f"📝 处理文本长度: {len(sample_text)} 字符")
        logger.info(f"📝 文本预览: {sample_text[:100]}...")
        
        # 运行简化工作流
        workflow.run_simplified_workflow(sample_text)
        
        logger.info("🎉 AutoGen知识图谱生成系统执行完成！")
        logger.info("💡 请检查Neo4j Browser查看生成的知识图谱")
        logger.info("🔍 查询命令: MATCH (n) RETURN n LIMIT 25")
        
    except KeyboardInterrupt:
        logger.info("\n⏹️ 程序被用户中断")
    except Exception as e:
        logger.error(f"💥 程序执行出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 