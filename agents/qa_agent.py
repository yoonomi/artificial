"""
问答智能体 (Question Answering Agent)

负责基于构建的知识图谱回答用户问题，提供图谱查询和推理功能。
"""

import autogen
from typing import Dict, List, Any, Optional, Tuple
import logging
import re
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Question:
    """问题数据类"""
    id: str
    text: str
    question_type: str
    entities_mentioned: List[str]
    relations_mentioned: List[str]
    complexity: str  # simple, medium, complex


@dataclass
class Answer:
    """答案数据类"""
    question_id: str
    answer_text: str
    confidence: float
    supporting_evidence: List[Dict[str, Any]]
    cypher_query: str
    reasoning_steps: List[str]


class QAAgent(autogen.AssistantAgent):
    """
    问答智能体
    
    职责:
    - 理解用户自然语言问题
    - 将问题转换为图谱查询
    - 基于知识图谱进行推理
    - 生成自然语言答案
    - 提供答案的支撑证据
    """
    
    def __init__(
        self,
        name: str = "QAAgent",
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
        
        self.knowledge_graph = None
        self.question_patterns = self._load_question_patterns()
        self.answered_questions = []
    
    def _get_default_system_message(self) -> str:
        """获取默认的系统消息"""
        return """你是一位知识图谱问答专家，能够理解自然语言问题并基于知识图谱提供准确答案。

你的主要职责包括:
1. 理解用户的自然语言问题，识别关键实体和关系
2. 将问题转换为图谱查询语句（如Cypher）
3. 基于知识图谱进行多步推理
4. 生成准确、完整的自然语言答案
5. 为答案提供可信的支撑证据和推理过程

请确保答案的准确性和可解释性，当信息不足时要明确说明。"""
    
    def load_knowledge_graph(self, knowledge_graph: Dict[str, Any]) -> None:
        """
        加载知识图谱
        
        Args:
            knowledge_graph: 知识图谱数据
        """
        self.knowledge_graph = knowledge_graph
        logger.info(f"已加载知识图谱：{len(knowledge_graph.get('nodes', []))} 个节点，{len(knowledge_graph.get('edges', []))} 条边")
    
    def answer_question(self, question_text: str) -> Dict[str, Any]:
        """
        回答问题的主要方法
        
        Args:
            question_text: 用户问题文本
            
        Returns:
            包含答案和相关信息的字典
        """
        try:
            logger.info(f"开始处理问题: {question_text}")
            
            if not self.knowledge_graph:
                raise ValueError("知识图谱未加载，无法回答问题")
            
            # 问题理解
            question = self._understand_question(question_text)
            
            # 实体识别和链接
            linked_entities = self._link_entities(question)
            
            # 查询生成
            cypher_query = self._generate_cypher_query(question, linked_entities)
            
            # 图谱查询执行（模拟）
            query_results = self._execute_graph_query(cypher_query)
            
            # 答案生成
            answer = self._generate_answer(question, query_results, cypher_query)
            
            # 记录问答历史
            self.answered_questions.append({
                "question": question,
                "answer": answer,
                "timestamp": self._get_current_timestamp()
            })
            
            result = {
                "question": self._question_to_dict(question),
                "answer": self._answer_to_dict(answer),
                "query_execution": {
                    "cypher_query": cypher_query,
                    "results_count": len(query_results),
                    "execution_success": True
                },
                "metadata": {
                    "qa_agent": self.name,
                    "processing_time": "simulated",
                    "graph_nodes_count": len(self.knowledge_graph.get('nodes', [])),
                    "graph_edges_count": len(self.knowledge_graph.get('edges', []))
                }
            }
            
            logger.info(f"问题处理完成，置信度: {answer.confidence}")
            return result
            
        except Exception as e:
            logger.error(f"回答问题时发生错误: {e}")
            raise
    
    def _understand_question(self, question_text: str) -> Question:
        """
        理解问题
        
        Args:
            question_text: 问题文本
            
        Returns:
            问题对象
        """
        question_id = f"Q{len(self.answered_questions)+1:04d}"
        
        # 问题类型识别
        question_type = self._classify_question_type(question_text)
        
        # 实体和关系提及识别
        entities_mentioned = self._extract_mentioned_entities(question_text)
        relations_mentioned = self._extract_mentioned_relations(question_text)
        
        # 复杂度评估
        complexity = self._assess_question_complexity(question_text, entities_mentioned, relations_mentioned)
        
        return Question(
            id=question_id,
            text=question_text,
            question_type=question_type,
            entities_mentioned=entities_mentioned,
            relations_mentioned=relations_mentioned,
            complexity=complexity
        )
    
    def _classify_question_type(self, question_text: str) -> str:
        """分类问题类型"""
        question_lower = question_text.lower()
        
        # 问题类型模式
        if any(word in question_lower for word in ['什么', '什么是', 'what']):
            return "definition"
        elif any(word in question_lower for word in ['哪里', '在哪', 'where']):
            return "location"
        elif any(word in question_lower for word in ['什么时候', '何时', 'when']):
            return "temporal"
        elif any(word in question_lower for word in ['谁', 'who']):
            return "person"
        elif any(word in question_lower for word in ['如何', '怎样', 'how']):
            return "method"
        elif any(word in question_lower for word in ['为什么', 'why']):
            return "causal"
        elif any(word in question_lower for word in ['多少', '数量', 'how many']):
            return "quantitative"
        elif any(word in question_lower for word in ['列出', '有哪些', 'list']):
            return "listing"
        else:
            return "general"
    
    def _extract_mentioned_entities(self, question_text: str) -> List[str]:
        """提取问题中提及的实体"""
        mentioned_entities = []
        
        if not self.knowledge_graph:
            return mentioned_entities
        
        nodes = self.knowledge_graph.get('nodes', [])
        
        # 简单的字符串匹配
        for node in nodes:
            node_label = node.get('label', '').lower()
            if len(node_label) > 1 and node_label in question_text.lower():
                mentioned_entities.append(node['id'])
        
        return mentioned_entities
    
    def _extract_mentioned_relations(self, question_text: str) -> List[str]:
        """提取问题中提及的关系"""
        mentioned_relations = []
        question_lower = question_text.lower()
        
        # 关系关键词映射
        relation_keywords = {
            "BELONGS_TO": ["属于", "隶属", "belong"],
            "LOCATED_IN": ["位于", "在", "located"],
            "FOUNDED": ["创立", "建立", "成立", "founded"],
            "OWNS": ["拥有", "持有", "own"],
            "IS_A": ["是", "为", "is"],
            "CONTAINS": ["包含", "包括", "contain"],
            "COOPERATES_WITH": ["合作", "协作", "cooperate"]
        }
        
        for relation_type, keywords in relation_keywords.items():
            if any(keyword in question_lower for keyword in keywords):
                mentioned_relations.append(relation_type)
        
        return mentioned_relations
    
    def _assess_question_complexity(self, question_text: str, entities: List[str], relations: List[str]) -> str:
        """评估问题复杂度"""
        complexity_score = 0
        
        # 基于实体数量
        complexity_score += len(entities)
        
        # 基于关系数量
        complexity_score += len(relations) * 2
        
        # 基于问题长度
        complexity_score += len(question_text.split()) * 0.1
        
        # 基于特殊词汇
        complex_words = ['比较', '关系', '影响', '导致', '结果', 'compare', 'relationship', 'influence']
        complexity_score += sum(1 for word in complex_words if word in question_text.lower())
        
        if complexity_score < 3:
            return "simple"
        elif complexity_score < 8:
            return "medium"
        else:
            return "complex"
    
    def _link_entities(self, question: Question) -> List[Dict[str, Any]]:
        """实体链接"""
        linked_entities = []
        
        if not self.knowledge_graph:
            return linked_entities
        
        nodes = self.knowledge_graph.get('nodes', [])
        
        for entity_id in question.entities_mentioned:
            entity_node = next((node for node in nodes if node['id'] == entity_id), None)
            if entity_node:
                linked_entities.append({
                    "entity_id": entity_id,
                    "entity_label": entity_node.get('label', ''),
                    "entity_type": entity_node.get('type', ''),
                    "confidence": 0.8
                })
        
        return linked_entities
    
    def _generate_cypher_query(self, question: Question, linked_entities: List[Dict[str, Any]]) -> str:
        """生成Cypher查询"""
        if not linked_entities:
            return "MATCH (n) RETURN n LIMIT 10"
        
        query_parts = []
        
        if question.question_type == "definition":
            # 定义类问题
            entity_id = linked_entities[0]['entity_id']
            query_parts.append(f"MATCH (n {{id: '{entity_id}'}})")
            query_parts.append("RETURN n.label, n.type, n.properties")
        
        elif question.question_type == "location":
            # 位置类问题
            entity_id = linked_entities[0]['entity_id']
            query_parts.append(f"MATCH (n {{id: '{entity_id}'}})-[r:LOCATED_IN]->(location)")
            query_parts.append("RETURN location.label, r")
        
        elif question.question_type == "temporal":
            # 时间类问题
            if linked_entities:
                entity_id = linked_entities[0]['entity_id']
                query_parts.append(f"MATCH (n {{id: '{entity_id}'}})-[r]-(event:TEMPORAL_EVENT)")
                query_parts.append("RETURN event.timestamp, event.event_type, r")
        
        elif question.question_type == "listing":
            # 列举类问题
            if question.relations_mentioned:
                relation_type = question.relations_mentioned[0]
                query_parts.append(f"MATCH (a)-[r:{relation_type}]->(b)")
                query_parts.append("RETURN a.label, b.label, r LIMIT 10")
        
        else:
            # 通用查询
            if len(linked_entities) == 1:
                entity_id = linked_entities[0]['entity_id']
                query_parts.append(f"MATCH (n {{id: '{entity_id}'}})-[r]-(connected)")
                query_parts.append("RETURN n, r, connected LIMIT 10")
            else:
                # 多实体查询
                entity_ids = [e['entity_id'] for e in linked_entities[:2]]
                query_parts.append(f"MATCH (a {{id: '{entity_ids[0]}'}}), (b {{id: '{entity_ids[1] if len(entity_ids) > 1 else entity_ids[0]}'}})")
                query_parts.append("MATCH path = (a)-[*1..3]-(b)")
                query_parts.append("RETURN path LIMIT 5")
        
        return " ".join(query_parts)
    
    def _execute_graph_query(self, cypher_query: str) -> List[Dict[str, Any]]:
        """执行图谱查询（模拟实现）"""
        # 这里模拟查询执行，实际应该连接到Neo4j数据库
        if not self.knowledge_graph:
            return []
        
        nodes = self.knowledge_graph.get('nodes', [])
        edges = self.knowledge_graph.get('edges', [])
        
        # 简单的模拟查询执行
        results = []
        
        # 模拟返回相关节点和边
        for node in nodes[:5]:  # 限制结果数量
            results.append({
                "type": "node",
                "data": node
            })
        
        for edge in edges[:3]:  # 限制结果数量
            results.append({
                "type": "edge", 
                "data": edge
            })
        
        return results
    
    def _generate_answer(self, question: Question, query_results: List[Dict[str, Any]], cypher_query: str) -> Answer:
        """生成答案"""
        if not query_results:
            return Answer(
                question_id=question.id,
                answer_text="抱歉，在知识图谱中没有找到相关信息来回答您的问题。",
                confidence=0.0,
                supporting_evidence=[],
                cypher_query=cypher_query,
                reasoning_steps=["无法在图谱中找到相关信息"]
            )
        
        # 根据问题类型生成答案
        answer_text = self._compose_answer_text(question, query_results)
        
        # 提取支撑证据
        supporting_evidence = self._extract_supporting_evidence(query_results)
        
        # 生成推理步骤
        reasoning_steps = self._generate_reasoning_steps(question, query_results)
        
        # 计算置信度
        confidence = self._calculate_answer_confidence(question, query_results)
        
        return Answer(
            question_id=question.id,
            answer_text=answer_text,
            confidence=confidence,
            supporting_evidence=supporting_evidence,
            cypher_query=cypher_query,
            reasoning_steps=reasoning_steps
        )
    
    def _compose_answer_text(self, question: Question, query_results: List[Dict[str, Any]]) -> str:
        """组合答案文本"""
        if not query_results:
            return "没有找到相关信息。"
        
        if question.question_type == "definition":
            nodes = [r['data'] for r in query_results if r['type'] == 'node']
            if nodes:
                node = nodes[0]
                return f"{node.get('label', '')} 是一个 {node.get('type', '')} 类型的实体。"
        
        elif question.question_type == "location":
            # 位置类答案
            edges = [r['data'] for r in query_results if r['type'] == 'edge' and 'LOCATED_IN' in r['data'].get('type', '')]
            if edges:
                return f"根据知识图谱，相关实体位于指定位置。"
        
        elif question.question_type == "listing":
            # 列举类答案
            nodes = [r['data'] for r in query_results if r['type'] == 'node']
            if len(nodes) > 1:
                node_labels = [node.get('label', '') for node in nodes[:5]]
                return f"找到以下相关实体：{', '.join(node_labels)}。"
        
        # 通用答案
        node_count = len([r for r in query_results if r['type'] == 'node'])
        edge_count = len([r for r in query_results if r['type'] == 'edge'])
        
        return f"基于知识图谱分析，找到了 {node_count} 个相关实体和 {edge_count} 个关系。具体信息请参考支撑证据。"
    
    def _extract_supporting_evidence(self, query_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """提取支撑证据"""
        evidence = []
        
        for result in query_results:
            if result['type'] == 'node':
                node_data = result['data']
                evidence.append({
                    "type": "entity",
                    "id": node_data.get('id', ''),
                    "label": node_data.get('label', ''),
                    "entity_type": node_data.get('type', ''),
                    "confidence": node_data.get('confidence', 0.0)
                })
            
            elif result['type'] == 'edge':
                edge_data = result['data']
                evidence.append({
                    "type": "relation",
                    "id": edge_data.get('id', ''),
                    "source": edge_data.get('source', ''),
                    "target": edge_data.get('target', ''),
                    "relation_type": edge_data.get('type', ''),
                    "confidence": edge_data.get('confidence', 0.0)
                })
        
        return evidence
    
    def _generate_reasoning_steps(self, question: Question, query_results: List[Dict[str, Any]]) -> List[str]:
        """生成推理步骤"""
        steps = []
        
        steps.append(f"1. 识别问题类型：{question.question_type}")
        steps.append(f"2. 提取关键实体：{len(question.entities_mentioned)} 个")
        steps.append(f"3. 生成图谱查询，匹配相关节点和关系")
        steps.append(f"4. 查询返回 {len(query_results)} 个结果")
        steps.append(f"5. 基于查询结果生成自然语言答案")
        
        return steps
    
    def _calculate_answer_confidence(self, question: Question, query_results: List[Dict[str, Any]]) -> float:
        """计算答案置信度"""
        if not query_results:
            return 0.0
        
        # 基础置信度
        base_confidence = 0.5
        
        # 根据结果数量调整
        result_factor = min(len(query_results) / 5.0, 1.0)
        
        # 根据问题复杂度调整
        complexity_factor = {
            "simple": 1.0,
            "medium": 0.8,
            "complex": 0.6
        }.get(question.complexity, 0.5)
        
        # 根据实体匹配度调整
        entity_factor = min(len(question.entities_mentioned) / 3.0, 1.0) if question.entities_mentioned else 0.3
        
        confidence = base_confidence * result_factor * complexity_factor * entity_factor
        return min(confidence, 0.95)  # 最大置信度限制
    
    def _load_question_patterns(self) -> List[Dict[str, Any]]:
        """加载问题模式"""
        return [
            {
                "pattern": r"(.+)是什么",
                "type": "definition",
                "complexity": "simple"
            },
            {
                "pattern": r"(.+)在哪里",
                "type": "location", 
                "complexity": "simple"
            },
            {
                "pattern": r"(.+)什么时候(.+)",
                "type": "temporal",
                "complexity": "medium"
            },
            {
                "pattern": r"列出(.+)",
                "type": "listing",
                "complexity": "medium"
            }
        ]
    
    def _get_current_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def _question_to_dict(self, question: Question) -> Dict[str, Any]:
        """将问题对象转换为字典"""
        return {
            "id": question.id,
            "text": question.text,
            "type": question.question_type,
            "entities_mentioned": question.entities_mentioned,
            "relations_mentioned": question.relations_mentioned,
            "complexity": question.complexity
        }
    
    def _answer_to_dict(self, answer: Answer) -> Dict[str, Any]:
        """将答案对象转换为字典"""
        return {
            "question_id": answer.question_id,
            "answer_text": answer.answer_text,
            "confidence": answer.confidence,
            "supporting_evidence": answer.supporting_evidence,
            "cypher_query": answer.cypher_query,
            "reasoning_steps": answer.reasoning_steps
        }
    
    def get_qa_statistics(self) -> Dict[str, Any]:
        """
        获取问答统计信息
        
        Returns:
            问答统计信息
        """
        if not self.answered_questions:
            return {"message": "暂无问答记录"}
        
        # 问题类型分布
        question_types = {}
        complexities = {}
        confidences = []
        
        for qa_record in self.answered_questions:
            q_type = qa_record['question'].question_type
            complexity = qa_record['question'].complexity
            confidence = qa_record['answer'].confidence
            
            question_types[q_type] = question_types.get(q_type, 0) + 1
            complexities[complexity] = complexities.get(complexity, 0) + 1
            confidences.append(confidence)
        
        return {
            "agent_name": self.name,
            "total_questions": len(self.answered_questions),
            "question_type_distribution": question_types,
            "complexity_distribution": complexities,
            "average_confidence": sum(confidences) / len(confidences),
            "high_confidence_answers": len([c for c in confidences if c > 0.7]),
            "knowledge_graph_loaded": self.knowledge_graph is not None
        } 