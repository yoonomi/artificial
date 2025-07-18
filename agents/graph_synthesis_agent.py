"""
图谱合成智能体 (Graph Synthesis Agent)

负责将所有智能体的输出整合，构建最终的知识图谱，并执行图谱优化和质量评估。
升级版：支持溯源信息处理和持久化。
"""

import autogen
from typing import Dict, List, Any, Optional, Set, Tuple
import logging
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)


@dataclass
class GraphNode:
    """图谱节点数据类"""
    id: str
    label: str
    type: str
    properties: Dict[str, Any]
    confidence: float
    source_sentence: Optional[str] = None  # 新增溯源信息


@dataclass
class GraphEdge:
    """图谱边数据类"""
    id: str
    source_id: str
    target_id: str
    relation_type: str
    properties: Dict[str, Any]
    confidence: float
    source_sentence: Optional[str] = None  # 新增溯源信息


def create_graph_synthesis_agent(llm_config: Dict[str, Any]) -> autogen.AssistantAgent:
    """
    创建图谱合成智能体
    
    Args:
        llm_config: LLM配置字典
        
    Returns:
        配置好的图谱合成智能体
    """
    
    system_message = """你是一个Neo4j Cypher代码生成器，负责将结构化的JSON数据精确地翻译成Neo4j的Cypher查询语句。

你的核心任务是处理包含溯源信息的实体和关系数据，并生成正确的Cypher查询来创建知识图谱。

**处理节点（实体）时的规则：**
- 当你接收到一个节点的JSON对象，如果它包含 `source_sentence` 字段，你必须在生成的 `MERGE` 查询中使用 `ON CREATE SET` 来添加这个属性
- 节点创建语法：`MERGE (n:Label {name: 'entity_name'}) ON CREATE SET n.source_sentence = 'complete_sentence', n.other_property = 'value'`
- 对于ECE智能体输出的实体，使用 `text` 字段作为 `name` 属性，使用 `label` 字段作为节点标签

**处理关系时的规则：**
- 当你接收到一个关系的JSON对象，如果它包含 `source_sentence` 字段，你必须在生成的关系创建查询中使用 `SET` 来添加这个属性
- 关系创建语法：`MATCH (a:Label1 {name: 'entity1'}), (b:Label2 {name: 'entity2'}) MERGE (a)-[r:RELATIONSHIP_TYPE]->(b) SET r.source_sentence = 'complete_sentence'`
- 对于REE智能体输出的关系，使用 `source_entity_id` 和 `target_entity_id` 来匹配对应的实体

**字符串转义规则：**
1. 将所有单引号 ' 替换为 \\'
2. 将所有反斜杠 \\ 替换为 \\\\
3. 将所有换行符 \\n 替换为空格

**重要要求：**
1. `source_sentence` 必须作为属性持久化到Neo4j数据库中
2. 使用 `MERGE` 而不是 `CREATE` 来避免重复节点
3. 确保所有的字符串值都正确转义
4. 生成的Cypher语句必须是有效的Neo4j语法
5. 每条语句必须是完整的，可以独立执行

**输出格式：**
返回一个包含 `cypher_statements` 数组的JSON对象，每个元素都是一条完整的Cypher语句。

示例输出：
```json
{
  "cypher_statements": [
    "MERGE (p:人物 {name: '爱因斯坦'}) ON CREATE SET p.source_sentence = '阿尔伯特·爱因斯坦是一位出生于德国的物理学家。', p.unique_id = 'entity_1'",
    "MERGE (l:机构 {name: '普林斯顿大学'}) ON CREATE SET l.source_sentence = '他曾在普林斯顿高等研究院工作。', l.unique_id = 'entity_2'",
    "MATCH (a:人物 {name: '爱因斯坦'}), (b:机构 {name: '普林斯顿大学'}) MERGE (a)-[r:工作于]->(b) SET r.source_sentence = '他曾在普林斯顿高等研究院工作。'"
  ]
}
```"""

    return autogen.AssistantAgent(
        name="GraphSynthesisAgent",
        system_message=system_message,
        llm_config=llm_config,
        max_consecutive_auto_reply=1,
        human_input_mode="NEVER",
        code_execution_config=False,
    )


class GraphSynthesisAgent(autogen.AssistantAgent):
    """
    图谱合成智能体（向后兼容的类版本）
    
    职责:
    - 整合所有智能体的输出结果
    - 构建统一的知识图谱结构
    - 执行图谱优化和去重
    - 计算图谱质量指标
    - 生成图谱统计报告
    - 支持溯源信息处理
    """
    
    def __init__(
        self,
        name: str = "GraphSynthesisAgent",
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
        
        self.graph_nodes = []
        self.graph_edges = []
        self.graph_metadata = {}
        self.quality_metrics = {}
    
    def _get_default_system_message(self) -> str:
        """获取默认的系统消息（升级版支持溯源信息）"""
        return """你是一位知识图谱合成专家，负责整合多个智能体的输出，构建高质量的知识图谱。

你的主要职责包括:
1. 整合来自不同智能体的实体、关系和时序信息
2. 处理和保留溯源信息（source_sentence字段）
3. 解决数据冲突和不一致性问题
4. 优化图谱结构，提高连通性和可查询性
5. 生成包含溯源信息的Cypher查询语句
6. 计算和评估图谱的质量指标
7. 生成详细的图谱构建报告和统计信息

特别注意：
- 确保所有的实体和关系都保留其source_sentence属性
- 在生成Cypher查询时正确处理溯源信息
- 维护数据的可追溯性和透明度

请确保最终图谱具有高质量、一致性、可追溯性和实用性。"""
    
    def synthesize_knowledge_graph(self, agent_outputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        合成知识图谱的主要方法（升级版）
        
        Args:
            agent_outputs: 各个智能体的输出结果
            
        Returns:
            最终的知识图谱结构
        """
        try:
            logger.info("开始知识图谱合成（支持溯源信息）...")
            
            # 提取各智能体的输出
            text_data = agent_outputs.get('text_deconstruction', {})
            extraction_data = agent_outputs.get('entity_relation_extraction', {})
            enhancement_data = agent_outputs.get('relation_enhancement', {})
            temporal_data = agent_outputs.get('temporal_analysis', {})
            ontology_data = agent_outputs.get('chief_ontologist', {})
            
            # 构建节点（支持溯源信息）
            nodes = self._build_graph_nodes_with_source(extraction_data, temporal_data, ontology_data)
            
            # 构建边（支持溯源信息）
            edges = self._build_graph_edges_with_source(extraction_data, enhancement_data, temporal_data)
            
            # 图谱优化
            optimized_nodes, optimized_edges = self._optimize_graph(nodes, edges)
            
            # 计算质量指标
            quality_metrics = self._calculate_quality_metrics(optimized_nodes, optimized_edges)
            
            # 生成图谱元数据
            metadata = self._generate_graph_metadata(agent_outputs, optimized_nodes, optimized_edges)
            
            self.graph_nodes = optimized_nodes
            self.graph_edges = optimized_edges
            self.graph_metadata = metadata
            self.quality_metrics = quality_metrics
            
            # 构建最终输出
            knowledge_graph = {
                "nodes": [self._node_to_dict_with_source(n) for n in optimized_nodes],
                "edges": [self._edge_to_dict_with_source(e) for e in optimized_edges],
                "metadata": metadata,
                "quality_metrics": quality_metrics,
                "statistics": self._generate_graph_statistics(optimized_nodes, optimized_edges),
                "cypher_queries": self._generate_sample_queries(optimized_nodes, optimized_edges),
                "neo4j_creation_queries": self._generate_neo4j_creation_queries_with_source(optimized_nodes, optimized_edges)
            }
            
            logger.info(f"知识图谱合成完成：{len(optimized_nodes)} 个节点，{len(optimized_edges)} 条边")
            return knowledge_graph
            
        except Exception as e:
            logger.error(f"知识图谱合成过程中发生错误: {e}")
            raise
    
    def _build_graph_nodes_with_source(self, extraction_data: Dict[str, Any], temporal_data: Dict[str, Any], ontology_data: Dict[str, Any]) -> List[GraphNode]:
        """
        构建图谱节点（支持溯源信息）
        
        Args:
            extraction_data: 实体抽取数据
            temporal_data: 时序分析数据
            ontology_data: 本体设计数据
            
        Returns:
            图谱节点列表
        """
        nodes = []
        entities = extraction_data.get('entities', [])
        temporal_events = temporal_data.get('temporal_events', [])
        
        # 创建实体节点（支持溯源信息）
        for entity in entities:
            # 获取溯源信息
            source_sentence = entity.get('source_sentence', '')
            
            node = GraphNode(
                id=entity.get('unique_id', entity.get('id', f"entity_{len(nodes)}")),
                label=entity.get('text', entity.get('label', '')),
                type=entity.get('label', entity.get('type', 'ENTITY')),
                properties={
                    'name': entity.get('text', ''),
                    'original_text': entity.get('text', ''),
                    'confidence': entity.get('confidence', 0.8),
                    'start_pos': entity.get('start_pos'),
                    'end_pos': entity.get('end_pos'),
                    'context': entity.get('attributes', {}).get('context', ''),
                    'extraction_method': 'entity_extraction'
                },
                confidence=entity.get('confidence', 0.8),
                source_sentence=source_sentence
            )
            nodes.append(node)
        
        # 创建时序事件节点
        for event in temporal_events:
            source_sentence = event.get('source_sentence', '')
            
            node = GraphNode(
                id=event.get('id', f"event_{len(nodes)}"),
                label=event.get('event_text', ''),
                type='TEMPORAL_EVENT',
                properties={
                    'event_type': event.get('event_type', ''),
                    'timestamp': event.get('timestamp', ''),
                    'time_expression': event.get('time_expression', ''),
                    'entities_involved': event.get('entities_involved', []),
                    'confidence': event.get('confidence', 0.8),
                    'extraction_method': 'temporal_analysis'
                },
                confidence=event.get('confidence', 0.8),
                source_sentence=source_sentence
            )
            nodes.append(node)
        
        return nodes
    
    def _build_graph_edges_with_source(self, extraction_data: Dict[str, Any], enhancement_data: Dict[str, Any], temporal_data: Dict[str, Any]) -> List[GraphEdge]:
        """
        构建图谱边（支持溯源信息）
        
        Args:
            extraction_data: 实体关系抽取数据
            enhancement_data: 关系增强数据
            temporal_data: 时序分析数据
            
        Returns:
            图谱边列表
        """
        edges = []
        
        # 处理基础关系（支持溯源信息）
        relations = extraction_data.get('relations', [])
        for relation in relations:
            source_sentence = relation.get('source_sentence', '')
            
            edge = GraphEdge(
                id=relation.get('id', f"rel_{len(edges)}"),
                source_id=relation.get('source_entity_id', relation.get('subject', '')),
                target_id=relation.get('target_entity_id', relation.get('object', '')),
                relation_type=relation.get('relationship_type', relation.get('predicate', 'RELATED_TO')),
                properties={
                    'confidence': relation.get('confidence', 0.8),
                    'context': relation.get('context', ''),
                    'extraction_method': 'relation_extraction'
                },
                confidence=relation.get('confidence', 0.8),
                source_sentence=source_sentence
            )
            edges.append(edge)
        
        # 处理增强关系
        enhanced_relations = enhancement_data.get('enhanced_relations', [])
        for relation in enhanced_relations:
            source_sentence = relation.get('source_sentence', '')
            
            edge = GraphEdge(
                id=relation.get('id', f"enhanced_rel_{len(edges)}"),
                source_id=relation.get('subject', ''),
                target_id=relation.get('object', ''),
                relation_type=relation.get('predicate', 'ENHANCED_RELATION'),
                properties={
                    'confidence': relation.get('confidence', 0.7),
                    'semantic_weight': relation.get('semantic_weight', 0.5),
                    'semantic_type': relation.get('semantic_type', ''),
                    'extraction_method': 'relation_enhancement'
                },
                confidence=relation.get('confidence', 0.7),
                source_sentence=source_sentence
            )
            edges.append(edge)
        
        # 处理时序关系
        temporal_relations = temporal_data.get('temporal_relations', [])
        for relation in temporal_relations:
            source_sentence = relation.get('source_sentence', '')
            
            edge = GraphEdge(
                id=relation.get('id', f"temporal_rel_{len(edges)}"),
                source_id=relation.get('source_entity', ''),
                target_id=relation.get('target_entity', ''),
                relation_type=relation.get('relation_type', 'TEMPORAL_RELATION'),
                properties={
                    'temporal_type': relation.get('temporal_type', ''),
                    'confidence': relation.get('confidence', 0.8),
                    'extraction_method': 'temporal_analysis'
                },
                confidence=relation.get('confidence', 0.8),
                source_sentence=source_sentence
            )
            edges.append(edge)
        
        return edges
    
    def _optimize_graph(self, nodes: List[GraphNode], edges: List[GraphEdge]) -> Tuple[List[GraphNode], List[GraphEdge]]:
        """
        优化图谱结构
        
        Args:
            nodes: 原始节点列表
            edges: 原始边列表
            
        Returns:
            优化后的节点和边列表
        """
        # 节点去重和合并
        optimized_nodes = self._merge_duplicate_nodes(nodes)
        
        # 边去重和合并
        optimized_edges = self._merge_duplicate_edges(edges)
        
        # 移除孤立节点
        connected_nodes = self._remove_isolated_nodes(optimized_nodes, optimized_edges)
        
        # 重新验证边的有效性
        valid_edges = self._validate_edges(optimized_edges, connected_nodes)
        
        return connected_nodes, valid_edges
    
    def _merge_duplicate_nodes(self, nodes: List[GraphNode]) -> List[GraphNode]:
        """合并重复节点"""
        node_map = {}
        
        for node in nodes:
            # 使用文本和类型作为合并依据
            key = (node.label.lower().strip(), node.type)
            
            if key in node_map:
                # 合并节点属性，保留置信度更高的
                existing_node = node_map[key]
                if node.confidence > existing_node.confidence:
                    # 合并属性
                    existing_node.properties.update(node.properties)
                    existing_node.confidence = max(existing_node.confidence, node.confidence)
            else:
                node_map[key] = node
        
        return list(node_map.values())
    
    def _merge_duplicate_edges(self, edges: List[GraphEdge]) -> List[GraphEdge]:
        """合并重复边"""
        edge_map = {}
        
        for edge in edges:
            # 使用源节点、目标节点和关系类型作为合并依据
            key = (edge.source_id, edge.target_id, edge.relation_type)
            
            if key in edge_map:
                # 保留置信度更高的边
                existing_edge = edge_map[key]
                if edge.confidence > existing_edge.confidence:
                    existing_edge.properties.update(edge.properties)
                    existing_edge.confidence = max(existing_edge.confidence, edge.confidence)
            else:
                edge_map[key] = edge
        
        return list(edge_map.values())
    
    def _remove_isolated_nodes(self, nodes: List[GraphNode], edges: List[GraphEdge]) -> List[GraphNode]:
        """移除孤立节点"""
        connected_node_ids = set()
        
        for edge in edges:
            connected_node_ids.add(edge.source_id)
            connected_node_ids.add(edge.target_id)
        
        return [node for node in nodes if node.id in connected_node_ids]
    
    def _validate_edges(self, edges: List[GraphEdge], nodes: List[GraphNode]) -> List[GraphEdge]:
        """验证边的有效性"""
        node_ids = {node.id for node in nodes}
        return [edge for edge in edges if edge.source_id in node_ids and edge.target_id in node_ids]
    
    def _calculate_quality_metrics(self, nodes: List[GraphNode], edges: List[GraphEdge]) -> Dict[str, Any]:
        """
        计算图谱质量指标
        
        Args:
            nodes: 节点列表
            edges: 边列表
            
        Returns:
            质量指标字典
        """
        if not nodes:
            return {"error": "No nodes in graph"}
        
        # 基本统计
        node_count = len(nodes)
        edge_count = len(edges)
        
        # 连通性指标
        avg_degree = (2 * edge_count) / node_count if node_count > 0 else 0
        
        # 置信度统计
        node_confidences = [node.confidence for node in nodes]
        edge_confidences = [edge.confidence for edge in edges]
        
        avg_node_confidence = sum(node_confidences) / len(node_confidences) if node_confidences else 0
        avg_edge_confidence = sum(edge_confidences) / len(edge_confidences) if edge_confidences else 0
        
        # 类型多样性
        node_types = set(node.type for node in nodes)
        edge_types = set(edge.relation_type for edge in edges)
        
        # 图密度
        max_edges = node_count * (node_count - 1) / 2 if node_count > 1 else 1
        density = edge_count / max_edges if max_edges > 0 else 0
        
        return {
            "node_count": node_count,
            "edge_count": edge_count,
            "average_degree": avg_degree,
            "graph_density": density,
            "average_node_confidence": avg_node_confidence,
            "average_edge_confidence": avg_edge_confidence,
            "node_type_diversity": len(node_types),
            "edge_type_diversity": len(edge_types),
            "node_types": list(node_types),
            "edge_types": list(edge_types)
        }
    
    def _generate_graph_metadata(self, agent_outputs: Dict[str, Any], nodes: List[GraphNode], edges: List[GraphEdge]) -> Dict[str, Any]:
        """生成图谱元数据"""
        from datetime import datetime
        
        return {
            "creation_timestamp": datetime.now().isoformat(),
            "synthesis_agent": self.name,
            "source_agents": list(agent_outputs.keys()),
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "processing_pipeline": [
                "text_deconstruction",
                "entity_relation_extraction", 
                "relation_enhancement",
                "temporal_analysis",
                "graph_synthesis"
            ],
            "version": "1.0"
        }
    
    def _generate_graph_statistics(self, nodes: List[GraphNode], edges: List[GraphEdge]) -> Dict[str, Any]:
        """生成详细的图谱统计信息"""
        # 节点类型分布
        node_type_dist = {}
        for node in nodes:
            node_type_dist[node.type] = node_type_dist.get(node.type, 0) + 1
        
        # 边类型分布
        edge_type_dist = {}
        for edge in edges:
            edge_type_dist[edge.relation_type] = edge_type_dist.get(edge.relation_type, 0) + 1
        
        # 度数分布
        degree_dist = {}
        for node in nodes:
            degree = sum(1 for edge in edges if edge.source_id == node.id or edge.target_id == node.id)
            degree_dist[node.id] = degree
        
        return {
            "node_type_distribution": node_type_dist,
            "edge_type_distribution": edge_type_dist,
            "degree_distribution": {
                "min_degree": min(degree_dist.values()) if degree_dist else 0,
                "max_degree": max(degree_dist.values()) if degree_dist else 0,
                "avg_degree": sum(degree_dist.values()) / len(degree_dist) if degree_dist else 0
            },
            "high_degree_nodes": [node_id for node_id, degree in degree_dist.items() if degree > 3]
        }
    
    def _generate_sample_queries(self, nodes: List[GraphNode], edges: List[GraphEdge]) -> List[Dict[str, str]]:
        """生成示例Cypher查询"""
        queries = []
        
        # 基本查询示例
        if nodes and edges:
            queries.extend([
                {
                    "description": "查找所有节点",
                    "cypher": "MATCH (n) RETURN n LIMIT 10"
                },
                {
                    "description": "查找所有关系",
                    "cypher": "MATCH (a)-[r]->(b) RETURN a, r, b LIMIT 10"
                },
                {
                    "description": "按节点类型查询",
                    "cypher": f"MATCH (n:{nodes[0].type}) RETURN n LIMIT 10"
                },
                {
                    "description": "查找高度连接的节点",
                    "cypher": "MATCH (n) WHERE size((n)--()) > 2 RETURN n, size((n)--()) as degree ORDER BY degree DESC"
                },
                {
                    "description": "查找两跳路径",
                    "cypher": "MATCH (a)-[r1]->(b)-[r2]->(c) RETURN a, r1, b, r2, c LIMIT 10"
                }
            ])
        
        # 基于实际关系类型的查询
        edge_types = set(edge.relation_type for edge in edges)
        for edge_type in list(edge_types)[:3]:  # 前3种关系类型
            queries.append({
                "description": f"查找{edge_type}关系",
                "cypher": f"MATCH (a)-[r:{edge_type}]->(b) RETURN a, r, b LIMIT 10"
            })
        
        return queries
    
    def _node_to_dict_with_source(self, node: GraphNode) -> Dict[str, Any]:
        """将节点对象转换为字典（包含溯源信息）"""
        result = {
            "id": node.id,
            "label": node.label,
            "type": node.type,
            "properties": node.properties,
            "confidence": node.confidence
        }
        if node.source_sentence:
            result["source_sentence"] = node.source_sentence
        return result
    
    def _edge_to_dict_with_source(self, edge: GraphEdge) -> Dict[str, Any]:
        """将边对象转换为字典（包含溯源信息）"""
        result = {
            "id": edge.id,
            "source_id": edge.source_id,
            "target_id": edge.target_id,
            "relation_type": edge.relation_type,
            "properties": edge.properties,
            "confidence": edge.confidence
        }
        if edge.source_sentence:
            result["source_sentence"] = edge.source_sentence
        return result
    
    def export_to_neo4j_format(self) -> Dict[str, List[str]]:
        """
        导出为Neo4j格式
        
        Returns:
            包含Cypher创建语句的字典
        """
        create_statements = []
        
        # 创建节点的Cypher语句
        for node in self.graph_nodes:
            properties_str = ", ".join([f"{k}: '{v}'" if isinstance(v, str) else f"{k}: {v}" 
                                     for k, v in node.properties.items()])
            create_stmt = f"CREATE (n:{node.type} {{id: '{node.id}', label: '{node.label}', {properties_str}}})"
            create_statements.append(create_stmt)
        
        # 创建关系的Cypher语句
        for edge in self.graph_edges:
            properties_str = ", ".join([f"{k}: '{v}'" if isinstance(v, str) else f"{k}: {v}" 
                                     for k, v in edge.properties.items()])
            match_stmt = f"MATCH (a {{id: '{edge.source_id}'}}), (b {{id: '{edge.target_id}'}}) CREATE (a)-[r:{edge.relation_type} {{{properties_str}}}]->(b)"
            create_statements.append(match_stmt)
        
        return {
            "cypher_statements": create_statements
        }
    
    def get_synthesis_statistics(self) -> Dict[str, Any]:
        """
        获取合成统计信息
        
        Returns:
            合成统计信息
        """
        return {
            "agent_name": self.name,
            "synthesized_nodes": len(self.graph_nodes),
            "synthesized_edges": len(self.graph_edges),
            "quality_metrics": self.quality_metrics,
            "graph_metadata": self.graph_metadata
        } 

    def _generate_neo4j_creation_queries_with_source(self, nodes: List[GraphNode], edges: List[GraphEdge]) -> List[str]:
        """
        生成包含溯源信息的Neo4j创建查询
        
        Args:
            nodes: 节点列表
            edges: 边列表
            
        Returns:
            Cypher查询语句列表
        """
        queries = []
        
        # 生成节点创建查询（支持溯源信息）
        for node in nodes:
            # 转义单引号
            label = node.label.replace("'", "\\'")
            node_type = node.type.replace("'", "\\'")
            
            # 构建属性字符串
            properties = []
            if node.properties.get('name'):
                name_value = node.properties['name'].replace("'", "\\'")
                properties.append(f"name: '{name_value}'")
            
            properties.append(f"confidence: {node.confidence}")
            
            # 构建基本的MERGE查询
            unique_property = f"name: '{label}'"
            merge_query = f"MERGE (n:{node_type} {{{unique_property}}})"
            
            # 添加ON CREATE SET子句
            set_properties = []
            if node.source_sentence:
                escaped_sentence = node.source_sentence.replace("'", "\\'")
                set_properties.append(f"n.source_sentence = '{escaped_sentence}'")
            
            for key, value in node.properties.items():
                if key != 'name':  # name已经在MERGE中使用
                    if isinstance(value, str):
                        escaped_value = value.replace("'", "\\'")
                        set_properties.append(f"n.{key} = '{escaped_value}'")
                    else:
                        set_properties.append(f"n.{key} = {value}")
            
            if set_properties:
                merge_query += f" ON CREATE SET {', '.join(set_properties)}"
            
            queries.append(merge_query)
        
        # 生成关系创建查询（支持溯源信息）
        for edge in edges:
            # 查找源节点和目标节点
            source_node = next((n for n in nodes if n.id == edge.source_id), None)
            target_node = next((n for n in nodes if n.id == edge.target_id), None)
            
            if source_node and target_node:
                source_label = source_node.label.replace("'", "\\'")
                target_label = target_node.label.replace("'", "\\'")
                relation_type = edge.relation_type.replace("'", "\\'")
                
                # 构建MATCH和MERGE查询
                match_query = f"MATCH (a:{source_node.type} {{name: '{source_label}'}}), (b:{target_node.type} {{name: '{target_label}'}})"
                merge_query = f"MERGE (a)-[r:{relation_type}]->(b)"
                
                # 添加SET子句设置溯源信息
                set_properties = []
                if edge.source_sentence:
                    escaped_sentence = edge.source_sentence.replace("'", "\\'")
                    set_properties.append(f"r.source_sentence = '{escaped_sentence}'")
                
                set_properties.append(f"r.confidence = {edge.confidence}")
                
                for key, value in edge.properties.items():
                    if isinstance(value, str):
                        escaped_value = value.replace("'", "\\'")
                        set_properties.append(f"r.{key} = '{escaped_value}'")
                    else:
                        set_properties.append(f"r.{key} = {value}")
                
                full_query = f"{match_query} {merge_query}"
                if set_properties:
                    full_query += f" SET {', '.join(set_properties)}"
                
                queries.append(full_query)
        
        return queries 