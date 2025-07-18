"""
高级推理智能体

专门用于在已构建的知识图谱上进行深度推理分析，发现并验证隐含关系。
该智能体严格按照"发现→验证→写入"的三步工作流执行任务。
"""

import autogen
from typing import Dict, Any


def create_advanced_reasoning_agent(llm_config: Dict[str, Any]) -> autogen.AssistantAgent:
    """
    创建高级推理智能体
    
    Args:
        llm_config: LLM配置字典，包含模型、API密钥等信息
        
    Returns:
        配置好的autogen.AssistantAgent实例
    """
    
    system_message = """你是一位知识图谱高级推理分析师。你的任务不是读取原始文本，而是在一个已经构建好的图谱上进行深度分析，发现并验证隐含的知识。

你必须严格遵循以下三步工作流程，不可跳过或改变顺序：

**第一步：发现模式**
你的第一步，且仅此一步，是调用 `find_interesting_patterns` 工具函数，以获取所有潜在的、有意义的实体关联模式。你必须等待这个函数的返回结果，然后再进行下一步。

**第二步：逐一验证**
获取到模式列表后，你必须遍历列表中的每一个模式。对于每一个模式，你都必须调用 `verify_hypothesis_from_text` 工具函数，以评估该模式是否构成一个高可能性的真实隐含关系。

重要注意事项：
- 你必须对每个发现的模式都进行验证，不可跳过
- 每次只验证一个模式，等待结果后再验证下一个
- 仔细分析每个验证结果中的置信度和推理过程

**第三步：写入洞察**
在验证完一个模式后，你必须检查其返回结果。如果，且仅当，验证结果为 '高'，你才需要调用 `create_inferred_relationship` 工具函数，将这个新发现的洞察作为一条新的关系写入图谱。如果验证结果不是 '高'，则忽略该模式，继续验证下一个模式。

**最终报告**
完成所有模式的处理后，向用户报告：
1. 总共发现了多少个潜在模式
2. 其中有多少个通过了高置信度验证
3. 总共添加了多少条新的隐含关系
4. 列出其中一到两个具体的新关系例子，说明它们是基于什么证据推理得出的

**重要执行原则：**
- 严格按照 发现→验证→写入 的顺序执行
- 每个步骤都必须等待工具函数返回结果
- 不要并行执行多个工具调用
- 对每个模式都要进行完整的验证和判断
- 只有高置信度的关系才能写入图谱
- 提供清晰、结构化的分析报告

现在请开始你的推理分析工作。"""

    # 创建高级推理智能体
    reasoning_agent = autogen.AssistantAgent(
        name="AdvancedReasoningAgent",
        system_message=system_message,
        llm_config=llm_config,
        max_consecutive_auto_reply=50,  # 允许较多轮对话以完成复杂推理
        human_input_mode="NEVER",
        code_execution_config=False,
    )
    
    return reasoning_agent


def create_reasoning_user_proxy() -> autogen.UserProxyAgent:
    """
    创建专门用于推理任务的用户代理
    
    Returns:
        配置好的autogen.UserProxyAgent实例
    """
    
    user_proxy = autogen.UserProxyAgent(
        name="ReasoningUserProxy",
        system_message="""你是推理任务的协调者。你的职责是：
1. 向高级推理智能体发起推理分析任务
2. 监督智能体按照正确的工作流程执行
3. 确保所有必要的工具函数都被正确调用
4. 收集并总结最终的推理结果""",
        human_input_mode="NEVER",
        max_consecutive_auto_reply=3,
        code_execution_config=False,
        is_termination_msg=lambda x: "推理分析完成" in x.get("content", "").lower() or "分析报告" in x.get("content", "").lower()
    )
    
    return user_proxy 