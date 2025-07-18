"""
实体与概念抽取智能体 (Entity and Concept Extraction Agent)

负责从文本中识别和抽取实体，并为每个实体提供溯源信息。
"""

import autogen
from typing import Dict, List, Any, Optional


def create_ece_agent(llm_config: Dict[str, Any], ontology_json: str) -> autogen.AssistantAgent:
    """
    创建实体与概念抽取智能体
    
    Args:
        llm_config: LLM配置字典
        ontology_json: 本体论JSON字符串
        
    Returns:
        配置好的实体抽取智能体
    """
    
    system_message = f"""你是一个实体与概念抽取器。你的唯一目标是根据提供的本体论，从以下文本块中识别所有实体。

本体定义如下：{ontology_json}

你的输出必须是一个JSON格式的对象列表。每个对象都必须包含以下四个键：
- `text`：实体原文（实体在文本中的确切词汇）
- `label`：实体标签（根据本体论确定的实体类型）
- `unique_id`：临时唯一标识符（格式为 "entity_" + 数字，如 "entity_1", "entity_2"）
- `source_sentence`：包含该实体的、未经修改的原始句子（必须是文本中的完整句子）

重要要求：
1. source_sentence 必须是原文中的完整句子，不可省略或修改
2. 每个实体都必须有对应的 source_sentence
3. 如果一个句子包含多个实体，该句子可以作为多个实体的 source_sentence
4. 确保 source_sentence 确实包含对应的实体文本
5. 不要添加任何解释文字，只返回JSON数组

输出格式示例：
[
  {{
    "text": "张三",
    "label": "人物", 
    "unique_id": "entity_1",
    "source_sentence": "张三是北京大学的教授，专门研究人工智能。"
  }},
  {{
    "text": "北京大学",
    "label": "机构",
    "unique_id": "entity_2", 
    "source_sentence": "张三是北京大学的教授，专门研究人工智能。"
  }}
]"""

    return autogen.AssistantAgent(
        name="ECEAgent",
        system_message=system_message,
        llm_config=llm_config,
        max_consecutive_auto_reply=1,
        human_input_mode="NEVER",
        code_execution_config=False,
    ) 