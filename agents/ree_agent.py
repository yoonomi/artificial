"""
关系与事件抽取智能体 (Relation and Event Extraction Agent)

负责识别实体间的关系，并为每个关系提供溯源信息。
"""

import autogen
from typing import Dict, List, Any, Optional


def create_ree_agent(llm_config: Dict[str, Any], entities_json: str, relationship_types: List[str]) -> autogen.AssistantAgent:
    """
    创建关系与事件抽取智能体
        
        Args:
        llm_config: LLM配置字典
        entities_json: 已识别的实体列表JSON字符串
        relationship_types: 关系类型列表
        
        Returns:
        配置好的关系抽取智能体
    """
    
    relationship_types_str = "、".join(relationship_types)
    
    system_message = f"""你是一个关系与事件分析专家。给定以下文本块和其中已识别的实体列表：{entities_json}

你的任务是识别实体间所有符合关系类型的关系：{relationship_types_str}

你的输出必须是严格的JSON格式的对象列表。对于每条关系，对象都必须包含以下四个键：
- `source_entity_id`：源实体的unique_id（必须来自提供的实体列表）
- `target_entity_id`：目标实体的unique_id（必须来自提供的实体列表）
- `relationship_type`：关系类型（必须从提供的关系类型列表中选择）
- `source_sentence`：证明该关系存在的最直接的原始句子（必须是文本中的完整句子）

重要要求：
1. source_sentence 必须是原文中能够明确证明两个实体间存在该关系的完整句子
2. 每个关系都必须有对应的 source_sentence
3. source_sentence 应该同时包含源实体和目标实体，或者能够清楚地表明它们之间的关系
4. 只识别能够从文本中明确推断出的关系，不要添加推测的关系
5. 确保 source_entity_id 和 target_entity_id 都存在于提供的实体列表中
6. 不要添加任何解释文字，只返回JSON数组

输出格式示例：
[
  {{
    "source_entity_id": "entity_1",
    "target_entity_id": "entity_2", 
    "relationship_type": "工作于",
    "source_sentence": "张三是北京大学的教授，专门研究人工智能。"
  }},
  {{
    "source_entity_id": "entity_1",
    "target_entity_id": "entity_3",
    "relationship_type": "研究",
    "source_sentence": "张三是北京大学的教授，专门研究人工智能。"
  }}
]"""

    return autogen.AssistantAgent(
        name="REEAgent",
        system_message=system_message,
        llm_config=llm_config,
        max_consecutive_auto_reply=1,
        human_input_mode="NEVER",
        code_execution_config=False,
    ) 