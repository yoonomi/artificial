"""
首席本体论专家智能体 (Chief Ontologist Agent)

负责整体知识图谱架构设计、本体模式定义以及协调其他智能体的工作。
"""

import autogen
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ChiefOntologist(autogen.AssistantAgent):
    """
    首席本体论专家智能体
    
    职责:
    - 设计知识图谱的本体架构
    - 定义实体类型和关系类型
    - 协调其他智能体的工作流程
    - 质量控制和最终审查
    """
    
    def __init__(
        self,
        name: str = "ChiefOntologist",
        system_message: Optional[str] = None,
        **kwargs
    ):
        if system_message is None:
            system_message = self._get_default_system_message()
        
        super().__init__(
            name=name,
            system_message=system_message,
            **kwargs
        )
        
        self.ontology_schema = {}
        self.entity_types = set()
        self.relation_types = set()
    
    def _get_default_system_message(self) -> str:
        """获取默认的系统消息"""
        return """你是一位首席本体论专家，负责知识图谱的整体架构设计。

你的主要职责包括:
1. 分析输入文本，设计合适的本体架构
2. 定义实体类型和关系类型的分类体系
3. 协调其他智能体的工作，确保整体流程的一致性
4. 对最终生成的知识图谱进行质量审查和优化建议

请始终保持专业性和准确性，确保生成的本体架构具有良好的可扩展性和实用性。"""
    
    def design_ontology_schema(self, domain_text: str) -> Dict[str, Any]:
        """
        根据领域文本设计本体架构
        
        Args:
            domain_text: 领域相关的文本内容
            
        Returns:
            包含本体架构信息的字典
        """
        try:
            # 这里可以集成LLM来分析文本并设计本体架构
            logger.info(f"正在为领域文本设计本体架构...")
            
            # 示例本体架构
            schema = {
                "entity_types": [],
                "relation_types": [],
                "constraints": [],
                "metadata": {
                    "created_by": self.name,
                    "domain": "general"
                }
            }
            
            self.ontology_schema = schema
            return schema
            
        except Exception as e:
            logger.error(f"设计本体架构时发生错误: {e}")
            raise
    
    def validate_extraction_results(self, extraction_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证抽取结果是否符合本体架构
        
        Args:
            extraction_results: 实体关系抽取结果
            
        Returns:
            验证后的结果和建议
        """
        try:
            logger.info("正在验证抽取结果...")
            
            validation_report = {
                "valid": True,
                "issues": [],
                "suggestions": [],
                "approved_entities": [],
                "approved_relations": []
            }
            
            return validation_report
            
        except Exception as e:
            logger.error(f"验证抽取结果时发生错误: {e}")
            raise
    
    def coordinate_workflow(self, task_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        协调工作流程
        
        Args:
            task_type: 任务类型
            data: 任务数据
            
        Returns:
            协调结果
        """
        try:
            logger.info(f"正在协调工作流程: {task_type}")
            
            coordination_result = {
                "next_agent": None,
                "instructions": "",
                "priority": "normal",
                "deadline": None
            }
            
            return coordination_result
            
        except Exception as e:
            logger.error(f"协调工作流程时发生错误: {e}")
            raise 


def create_chief_ontologist_agent(llm_config: Optional[Dict] = None) -> autogen.AssistantAgent:
    """
    创建首席本体论专家智能体
    
    Args:
        llm_config: LLM配置，如果不提供则使用默认配置
        
    Returns:
        配置好的autogen.AssistantAgent实例
    """
    
    system_message = """你是一位世界顶级的本体论专家和知识图谱架构师。

你的任务是分析给定的文本内容，设计一个简洁而有效的知识图谱本体（Schema）。

职责:
1. 仔细阅读和理解输入的文本内容
2. 识别文本中的主要概念类型（实体类型）
3. 识别概念之间的关系类型
4. 设计一个简洁、通用且可扩展的本体架构

输出要求:
- 你的回复必须是一个严格的JSON对象，不要包含任何其他文字说明
- JSON必须包含以下两个键：
  * "node_labels": 一个字符串数组，包含识别出的实体类型（如["Person", "Organization", "Location"]）
  * "relationship_types": 一个字符串数组，包含识别出的关系类型（如["WORKS_AT", "LOCATED_IN", "DEVELOPED"]）

设计原则:
- 保持标签简洁明了，使用英文
- 确保标签具有通用性，不要过于具体
- 优先使用标准的本体概念
- 关系类型使用大写字母和下划线命名（如"WORKS_AT"）
- 实体类型使用首字母大写的驼峰命名（如"Person"）

示例输出格式:
{
  "node_labels": ["Person", "Organization", "Theory", "Location"],
  "relationship_types": ["DEVELOPED", "WORKS_AT", "LOCATED_IN"]
}"""

    # 设置默认LLM配置
    if llm_config is None:
        llm_config = {
            "model": "deepseek-ai/DeepSeek-V3",
            "temperature": 0.1,
            "max_tokens": 2000,
        }
    
    # 创建并返回智能体
    agent = autogen.AssistantAgent(
        name="ChiefOntologist",
        system_message=system_message,
        llm_config=llm_config,
        max_consecutive_auto_reply=1,  # 限制自动回复次数，确保输出简洁
    )
    
    logger.info("首席本体论专家智能体已创建")
    return agent 