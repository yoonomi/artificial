"""
AutoGen知识图谱生成系统 - 完整工作流集成

这是系统的主入口文件，使用AutoGen的GroupChat功能协调多个AI智能体
协同完成从文本到知识图谱的完整转换流程。
"""

import asyncio
import autogen
import logging
import sys
import json
from pathlib import Path
from typing import Dict, List, Any, Optional

# 导入配置和工具
from config import config
from tools.graph_db import GraphDB
from tools.text_processing import TextProcessor

# 导入现有的智能体类
from agents.chief_ontologist import create_chief_ontologist_agent
from agents.text_deconstruction_agent import TextDeconstructionAgent
from agents.ece_agent import ECEAgent
from agents.ree_agent import REEAgent
from agents.temporal_analyst_agent import TemporalAnalystAgent
from agents.graph_synthesis_agent import GraphSynthesisAgent

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout
)
logger = logging.getLogger(__name__)


def create_text_analyst_agent(llm_config: Dict) -> autogen.AssistantAgent:
    """创建文本分析智能体（基于AutoGen）"""
    
    system_message = """你是一位专业的文本分析专家。

职责：
1. 接收原始文本并进行深度分析
2. 识别文本的结构、主题和关键信息
3. 将文本分解为适合进一步处理的段落
4. 输出结构化的分析结果

输出格式：
请以JSON格式输出分析结果，包含以下字段：
{
  "summary": "文本总结",
  "main_topics": ["主题1", "主题2", ...],
  "segments": [
    {
      "id": 1,
      "content": "段落内容",
      "topic": "段落主题",
      "key_concepts": ["概念1", "概念2", ...]
    }
  ],
  "text_type": "文本类型",
  "complexity": "复杂度评估"
}"""

    return autogen.AssistantAgent(
        name="TextAnalyst",
        system_message=system_message,
        llm_config=llm_config,
        max_consecutive_auto_reply=1,
    )


def create_entity_extractor_agent(llm_config: Dict) -> autogen.AssistantAgent:
    """创建实体抽取智能体（基于AutoGen）"""
    
    system_message = """你是一位专业的实体识别专家。

职责：
1. 根据本体架构分析文本段落
2. 识别文本中的所有重要实体
3. 为每个实体确定类型和属性
4. 识别实体之间的关系

输出格式：
请以JSON格式输出抽取结果：
{
  "entities": [
    {
      "id": "E001",
      "text": "实体文本",
      "type": "实体类型",
      "properties": {
        "属性名": "属性值"
      },
      "start_pos": 0,
      "end_pos": 10,
      "confidence": 0.95
    }
  ],
  "relations": [
    {
      "id": "R001",
      "source_entity": "E001",
      "target_entity": "E002",
      "relation_type": "关系类型",
      "confidence": 0.90,
      "evidence": "支撑证据"
    }
  ]
}"""

    return autogen.AssistantAgent(
        name="EntityExtractor",
        system_message=system_message,
        llm_config=llm_config,
        max_consecutive_auto_reply=1,
    )


def create_knowledge_synthesizer_agent(llm_config: Dict) -> autogen.AssistantAgent:
    """创建知识合成智能体（基于AutoGen）"""
    
    system_message = """你是一位知识图谱合成专家。

职责：
1. 整合来自不同阶段的抽取结果
2. 消除重复实体和关系
3. 验证知识的一致性
4. 生成最终的知识图谱结构

输出格式：
请以JSON格式输出最终的知识图谱：
{
  "nodes": [
    {
      "id": "N001",
      "label": "节点标签",
      "type": "节点类型",
      "properties": {
        "name": "节点名称",
        "description": "描述",
        "confidence": 0.95
      }
    }
  ],
  "edges": [
    {
      "id": "E001", 
      "source": "N001",
      "target": "N002",
      "type": "关系类型",
      "properties": {
        "confidence": 0.90,
        "evidence": "支撑证据"
      }
    }
  ],
  "metadata": {
    "node_count": 10,
    "edge_count": 15,
    "creation_time": "ISO时间戳"
  }
}"""

    return autogen.AssistantAgent(
        name="KnowledgeSynthesizer",
        system_message=system_message,
        llm_config=llm_config,
        max_consecutive_auto_reply=1,
    )


def create_database_manager_agent(llm_config: Dict) -> autogen.AssistantAgent:
    """创建数据库管理智能体（基于AutoGen）"""
    
    system_message = """你是一位Neo4j数据库管理专家。

职责：
1. 接收知识图谱数据
2. 验证数据格式的正确性
3. 将数据保存到Neo4j数据库
4. 报告保存结果和统计信息

输出格式：
请以JSON格式报告处理结果：
{
  "status": "success/failed",
  "message": "处理消息",
  "statistics": {
    "nodes_created": 10,
    "relationships_created": 15,
    "processing_time": "处理时间"
  },
  "database_info": {
    "total_nodes": 100,
    "total_relationships": 200
  }
}"""

    return autogen.AssistantAgent(
        name="DatabaseManager",
        system_message=system_message,
        llm_config=llm_config,
        max_consecutive_auto_reply=1,
    )


class KnowledgeGraphWorkflow:
    """知识图谱生成工作流管理器"""
    
    def __init__(self):
        self.config = config
        self.llm_config = self.config.llm_config_gpt4
        self.graph_db = None
        self.workflow_results = {}
        
        # 初始化数据库连接
        self._init_database()
        
        # 创建所有智能体
        self.agents = self._create_agents()
        
        # 创建用户代理
        self.user_proxy = autogen.UserProxyAgent(
            name="UserProxy",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=0,
            code_execution_config=False,
        )
    
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
    
    def _create_agents(self) -> List[autogen.Agent]:
        """创建所有智能体"""
        logger.info("🤖 正在创建智能体...")
        
        agents = [
            create_chief_ontologist_agent(self.llm_config),
            create_text_analyst_agent(self.llm_config),
            create_entity_extractor_agent(self.llm_config),
            create_knowledge_synthesizer_agent(self.llm_config),
            create_database_manager_agent(self.llm_config),
        ]
        
        logger.info(f"✅ 成功创建 {len(agents)} 个智能体")
        return agents
    
    def _create_group_chat(self) -> autogen.GroupChat:
        """创建群组聊天"""
        # 定义发言顺序
        allowed_or_disallowed_speaker_transitions = {
            self.user_proxy: self.agents,  # 用户可以向任何智能体发起对话
            self.agents[0]: [self.agents[1]],  # ChiefOntologist -> TextAnalyst
            self.agents[1]: [self.agents[2]],  # TextAnalyst -> EntityExtractor
            self.agents[2]: [self.agents[3]],  # EntityExtractor -> KnowledgeSynthesizer
            self.agents[3]: [self.agents[4]],  # KnowledgeSynthesizer -> DatabaseManager
            self.agents[4]: [self.user_proxy],  # DatabaseManager -> UserProxy (结束)
        }
        
        group_chat = autogen.GroupChat(
            agents=[self.user_proxy] + self.agents,
            messages=[],
            max_round=20,  # 限制最大轮数
            allowed_or_disallowed_speaker_transitions=allowed_or_disallowed_speaker_transitions,
            speaker_transitions_type="allowed",
        )
        
        return group_chat
    
    def _create_group_chat_manager(self, group_chat: autogen.GroupChat) -> autogen.GroupChatManager:
        """创建群组聊天管理器"""
        return autogen.GroupChatManager(
            groupchat=group_chat,
            llm_config=self.llm_config,
            system_message="""你是知识图谱生成工作流的协调者。

你的职责是：
1. 确保智能体按照正确的顺序进行对话
2. 监控每个阶段的输出质量
3. 在必要时提供指导和澄清
4. 确保整个流程顺利完成

工作流顺序：
1. ChiefOntologist: 设计本体架构
2. TextAnalyst: 分析文本结构
3. EntityExtractor: 抽取实体和关系
4. KnowledgeSynthesizer: 合成知识图谱
5. DatabaseManager: 保存到数据库

请确保每个智能体的输出符合预期格式，并在适当时候推进到下一个阶段。"""
        )
    
    def load_sample_text(self, file_path: str = "data/sample_text.txt") -> str:
        """加载示例文本"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read().strip()
            logger.info(f"📖 成功加载文本文件: {file_path} ({len(text)} 字符)")
            return text
        except Exception as e:
            logger.error(f"❌ 加载文本文件失败: {e}")
            # 返回备用文本
            return """
人工智能技术发展历程

1950年，阿兰·图灵提出了图灵测试。
1956年，约翰·麦卡锡在达特茅斯会议上首次提出"人工智能"概念。
2016年，谷歌的AlphaGo击败了围棋世界冠军李世石。
2022年，OpenAI发布了ChatGPT，引发了新一轮AI热潮。
            """.strip()
    
    def run_workflow(self, input_text: str):
        """运行完整的知识图谱生成工作流"""
        logger.info("🚀 开始知识图谱生成工作流...")
        
        # 创建群组聊天
        group_chat = self._create_group_chat()
        manager = self._create_group_chat_manager(group_chat)
        
        # 构建初始任务消息
        initial_message = f"""
请协同完成从以下文本生成知识图谱的任务：

=== 输入文本 ===
{input_text}

=== 任务说明 ===
1. 首席本体论家：请首先分析文本并设计本体架构（实体类型和关系类型）
2. 文本分析师：基于本体架构分析文本结构
3. 实体抽取师：抽取文本中的实体和关系
4. 知识合成师：整合所有信息生成知识图谱
5. 数据库管理员：将知识图谱保存到Neo4j数据库

请开始执行，首席本体论家请先开始工作。
"""
        
        try:
            # 启动群组对话
            self.user_proxy.initiate_chat(
                manager,
                message=initial_message,
                max_turns=10
            )
            
            logger.info("✅ 工作流执行完成")
        
    except Exception as e:
            logger.error(f"❌ 工作流执行失败: {e}")
        raise

    def save_to_database(self, knowledge_graph: Dict[str, Any]) -> bool:
        """保存知识图谱到数据库"""
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


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("🧠 AutoGen知识图谱生成系统启动")
    logger.info("=" * 60)
    
    try:
        # 检查API密钥配置
        if not config.OPENAI_API_KEY or config.OPENAI_API_KEY == "your_openai_api_key_here":
            logger.error("❌ OpenAI API密钥未配置，请检查.env文件")
            return
        
        # 创建工作流管理器
        workflow = KnowledgeGraphWorkflow()
        
        # 加载示例文本
        sample_text = workflow.load_sample_text()
        
        logger.info(f"📝 处理文本长度: {len(sample_text)} 字符")
        logger.info(f"📝 文本预览: {sample_text[:200]}...")
        
        # 运行工作流
        workflow.run_workflow(sample_text)
        
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