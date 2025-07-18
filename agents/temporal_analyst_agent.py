"""
时序分析智能体 (Temporal Analyst Agent)

负责分析文本中的时间信息，构建时序关系，为知识图谱添加时间维度。
"""

import autogen
from typing import Dict, List, Any, Optional, Tuple
import logging
import re
from datetime import datetime, date
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TemporalEvent:
    """时序事件数据类"""
    id: str
    event_text: str
    timestamp: Optional[datetime]
    time_expression: str
    event_type: str
    entities_involved: List[str]
    confidence: float


@dataclass
class TemporalRelation:
    """时序关系数据类"""
    id: str
    event1_id: str
    event2_id: str
    relation_type: str  # BEFORE, AFTER, DURING, OVERLAPS, etc.
    confidence: float


class TemporalAnalystAgent(autogen.AssistantAgent):
    """
    时序分析智能体
    
    职责:
    - 识别文本中的时间表达式
    - 抽取时序事件
    - 建立事件之间的时序关系
    - 为知识图谱添加时间维度
    """
    
    def __init__(
        self,
        name: str = "TemporalAnalystAgent",
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
        
        self.temporal_events = []
        self.temporal_relations = []
        self.event_counter = 0
        self.relation_counter = 0
    
    def _get_default_system_message(self) -> str:
        """获取默认的系统消息"""
        return """你是一位时序分析专家，专门负责文本中时间信息的识别和分析。

你的主要职责包括:
1. 识别文本中的各种时间表达式（绝对时间、相对时间等）
2. 抽取与时间相关的事件和活动
3. 建立事件之间的时序关系（先后、并发、包含等）
4. 为知识图谱添加时间维度，支持时序查询和推理
5. 处理时间的不确定性和模糊性

请确保时间信息的准确性，合理处理时间的歧义性。"""
    
    def analyze_temporal_information(self, extraction_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析时序信息的主要方法
        
        Args:
            extraction_data: 实体关系抽取结果
            
        Returns:
            时序分析结果
        """
        try:
            logger.info("开始时序信息分析...")
            
            entities = extraction_data.get('entities', [])
            relations = extraction_data.get('relations', [])
            
            # 识别时间表达式
            time_expressions = self._extract_time_expressions(extraction_data)
            
            # 抽取时序事件
            temporal_events = self._extract_temporal_events(extraction_data, entities, time_expressions)
            
            # 建立时序关系
            temporal_relations = self._establish_temporal_relations(temporal_events)
            
            # 增强现有关系的时间信息
            enhanced_relations = self._enhance_relations_with_time(relations, temporal_events)
            
            self.temporal_events = temporal_events
            self.temporal_relations = temporal_relations
            
            result = {
                "time_expressions": time_expressions,
                "temporal_events": [self._event_to_dict(e) for e in temporal_events],
                "temporal_relations": [self._temporal_relation_to_dict(r) for r in temporal_relations],
                "enhanced_relations": enhanced_relations,
                "temporal_statistics": {
                    "time_expressions_count": len(time_expressions),
                    "temporal_events_count": len(temporal_events),
                    "temporal_relations_count": len(temporal_relations),
                    "time_coverage": self._calculate_time_coverage(temporal_events)
                },
                "metadata": {
                    "temporal_analyst": self.name,
                    "analysis_timestamp": datetime.now().isoformat()
                }
            }
            
            logger.info(f"时序分析完成：{len(temporal_events)} 个时序事件，{len(temporal_relations)} 个时序关系")
            return result
            
        except Exception as e:
            logger.error(f"时序分析过程中发生错误: {e}")
            raise
    
    def _extract_time_expressions(self, extraction_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        抽取时间表达式
        
        Args:
            extraction_data: 抽取数据
            
        Returns:
            时间表达式列表
        """
        time_expressions = []
        segments = extraction_data.get('segments', [])
        
        # 时间表达式的正则模式
        time_patterns = {
            "absolute_date": r'(\d{4})年(\d{1,2})月(\d{1,2})日',
            "year_month": r'(\d{4})年(\d{1,2})月',
            "year_only": r'(\d{4})年',
            "relative_time": r'(今天|昨天|明天|前天|后天|上周|下周|上月|下月|去年|明年)',
            "duration": r'(\d+)(年|月|日|小时|分钟|秒钟?)',
            "period": r'(春天|夏天|秋天|冬天|上午|下午|晚上|凌晨|深夜)',
            "dynasty": r'(春秋|战国|秦朝|汉朝|唐朝|宋朝|元朝|明朝|清朝)',
            "age_expression": r'(\d+)岁|(\d+)世纪'
        }
        
        for segment_idx, segment in enumerate(segments):
            for pattern_name, pattern in time_patterns.items():
                matches = re.finditer(pattern, segment)
                for match in matches:
                    time_expr = {
                        "id": f"TIME_{len(time_expressions)+1:03d}",
                        "text": match.group(),
                        "type": pattern_name,
                        "segment_id": segment_idx,
                        "start_pos": match.start(),
                        "end_pos": match.end(),
                        "normalized_time": self._normalize_time_expression(match.group(), pattern_name),
                        "context": segment[max(0, match.start()-30):match.end()+30]
                    }
                    time_expressions.append(time_expr)
        
        return time_expressions
    
    def _normalize_time_expression(self, time_text: str, time_type: str) -> Optional[str]:
        """
        标准化时间表达式
        
        Args:
            time_text: 时间文本
            time_type: 时间类型
            
        Returns:
            标准化的时间字符串
        """
        try:
            if time_type == "absolute_date":
                match = re.match(r'(\d{4})年(\d{1,2})月(\d{1,2})日', time_text)
                if match:
                    year, month, day = match.groups()
                    return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            
            elif time_type == "year_month":
                match = re.match(r'(\d{4})年(\d{1,2})月', time_text)
                if match:
                    year, month = match.groups()
                    return f"{year}-{month.zfill(2)}"
            
            elif time_type == "year_only":
                match = re.match(r'(\d{4})年', time_text)
                if match:
                    return match.group(1)
            
            # 相对时间需要根据当前时间计算
            elif time_type == "relative_time":
                # 这里简化处理，实际应该根据文档创建时间计算
                return time_text
            
            return time_text
            
        except Exception:
            return time_text
    
    def _extract_temporal_events(self, extraction_data: Dict[str, Any], entities: List[Dict[str, Any]], time_expressions: List[Dict[str, Any]]) -> List[TemporalEvent]:
        """
        抽取时序事件
        
        Args:
            extraction_data: 抽取数据
            entities: 实体列表
            time_expressions: 时间表达式列表
            
        Returns:
            时序事件列表
        """
        temporal_events = []
        segments = extraction_data.get('segments', [])
        
        # 事件动词模式
        event_patterns = [
            r'(创立|建立|成立|创建|建造)',
            r'(发生|出现|产生|形成)',
            r'(开始|启动|开启|发起)',
            r'(结束|完成|终止|停止)',
            r'(发布|发表|公布|宣布)',
            r'(签署|签订|达成|制定)',
            r'(去世|逝世|死亡|牺牲)',
            r'(出生|诞生|生于)',
            r'(迁移|搬迁|移居|转移)',
            r'(合并|收购|兼并|分拆)'
        ]
        
        for segment_idx, segment in enumerate(segments):
            # 查找该段落中的时间表达式
            segment_times = [te for te in time_expressions if te['segment_id'] == segment_idx]
            
            # 查找该段落中的实体
            segment_entities = [e for e in entities if e.get('attributes', {}).get('segment_id') == segment_idx]
            
            # 查找事件动词
            for pattern in event_patterns:
                matches = re.finditer(pattern, segment)
                for match in matches:
                    event_id = f"EVENT_{self.event_counter:04d}"
                    self.event_counter += 1
                    
                    # 查找最近的时间表达式
                    nearest_time = self._find_nearest_time_expression(match.start(), segment_times)
                    
                    # 查找相关实体
                    involved_entities = self._find_entities_in_context(
                        match.start(), match.end(), segment_entities
                    )
                    
                    event = TemporalEvent(
                        id=event_id,
                        event_text=segment[max(0, match.start()-20):match.end()+20],
                        timestamp=self._parse_timestamp(nearest_time) if nearest_time else None,
                        time_expression=nearest_time['text'] if nearest_time else "",
                        event_type=match.group(),
                        entities_involved=[e['id'] for e in involved_entities],
                        confidence=0.7
                    )
                    temporal_events.append(event)
        
        return temporal_events
    
    def _find_nearest_time_expression(self, position: int, time_expressions: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """查找最近的时间表达式"""
        if not time_expressions:
            return None
        
        nearest = None
        min_distance = float('inf')
        
        for time_expr in time_expressions:
            distance = abs(position - time_expr['start_pos'])
            if distance < min_distance:
                min_distance = distance
                nearest = time_expr
        
        return nearest if min_distance < 100 else None  # 距离阈值
    
    def _find_entities_in_context(self, start_pos: int, end_pos: int, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """查找上下文中的相关实体"""
        context_entities = []
        context_window = 50  # 上下文窗口大小
        
        for entity in entities:
            entity_start = entity.get('start_pos', 0)
            entity_end = entity.get('end_pos', 0)
            
            # 检查实体是否在事件的上下文窗口内
            if (abs(entity_start - start_pos) <= context_window or 
                abs(entity_end - end_pos) <= context_window):
                context_entities.append(entity)
        
        return context_entities
    
    def _parse_timestamp(self, time_expression: Dict[str, Any]) -> Optional[datetime]:
        """解析时间戳"""
        try:
            normalized_time = time_expression.get('normalized_time')
            if not normalized_time:
                return None
            
            time_type = time_expression.get('type')
            
            if time_type == "absolute_date":
                return datetime.strptime(normalized_time, "%Y-%m-%d")
            elif time_type == "year_month":
                return datetime.strptime(normalized_time + "-01", "%Y-%m-%d")
            elif time_type == "year_only":
                return datetime.strptime(normalized_time + "-01-01", "%Y-%m-%d")
            
            return None
            
        except Exception:
            return None
    
    def _establish_temporal_relations(self, temporal_events: List[TemporalEvent]) -> List[TemporalRelation]:
        """建立时序关系"""
        temporal_relations = []
        
        # 根据时间戳建立BEFORE/AFTER关系
        events_with_time = [e for e in temporal_events if e.timestamp]
        events_with_time.sort(key=lambda x: x.timestamp)
        
        for i in range(len(events_with_time) - 1):
            event1 = events_with_time[i]
            event2 = events_with_time[i + 1]
            
            relation_id = f"TREL_{self.relation_counter:04d}"
            self.relation_counter += 1
            
            relation = TemporalRelation(
                id=relation_id,
                event1_id=event1.id,
                event2_id=event2.id,
                relation_type="BEFORE",
                confidence=0.9
            )
            temporal_relations.append(relation)
        
        return temporal_relations
    
    def _enhance_relations_with_time(self, relations: List[Dict[str, Any]], temporal_events: List[TemporalEvent]) -> List[Dict[str, Any]]:
        """为现有关系添加时间信息"""
        enhanced_relations = []
        
        for relation in relations:
            enhanced_relation = relation.copy()
            
            # 查找涉及该关系实体的时序事件
            subject_events = [e for e in temporal_events if relation['subject'] in e.entities_involved]
            object_events = [e for e in temporal_events if relation['object'] in e.entities_involved]
            
            if subject_events or object_events:
                enhanced_relation['temporal_context'] = {
                    "subject_events": [e.id for e in subject_events],
                    "object_events": [e.id for e in object_events],
                    "temporal_validity": self._determine_temporal_validity(subject_events, object_events)
                }
            
            enhanced_relations.append(enhanced_relation)
        
        return enhanced_relations
    
    def _determine_temporal_validity(self, subject_events: List[TemporalEvent], object_events: List[TemporalEvent]) -> Dict[str, Any]:
        """确定关系的时间有效性"""
        validity = {
            "start_time": None,
            "end_time": None,
            "is_ongoing": True
        }
        
        all_events = subject_events + object_events
        events_with_time = [e for e in all_events if e.timestamp]
        
        if events_with_time:
            timestamps = [e.timestamp for e in events_with_time]
            validity["start_time"] = min(timestamps).isoformat()
            validity["end_time"] = max(timestamps).isoformat()
        
        return validity
    
    def _calculate_time_coverage(self, temporal_events: List[TemporalEvent]) -> Dict[str, Any]:
        """计算时间覆盖范围"""
        events_with_time = [e for e in temporal_events if e.timestamp]
        
        if not events_with_time:
            return {"coverage": "none"}
        
        timestamps = [e.timestamp for e in events_with_time]
        earliest = min(timestamps)
        latest = max(timestamps)
        
        return {
            "earliest_event": earliest.isoformat(),
            "latest_event": latest.isoformat(),
            "time_span_days": (latest - earliest).days,
            "events_with_timestamps": len(events_with_time),
            "total_events": len(temporal_events)
        }
    
    def _event_to_dict(self, event: TemporalEvent) -> Dict[str, Any]:
        """将时序事件对象转换为字典"""
        return {
            "id": event.id,
            "event_text": event.event_text,
            "timestamp": event.timestamp.isoformat() if event.timestamp else None,
            "time_expression": event.time_expression,
            "event_type": event.event_type,
            "entities_involved": event.entities_involved,
            "confidence": event.confidence
        }
    
    def _temporal_relation_to_dict(self, relation: TemporalRelation) -> Dict[str, Any]:
        """将时序关系对象转换为字典"""
        return {
            "id": relation.id,
            "event1_id": relation.event1_id,
            "event2_id": relation.event2_id,
            "relation_type": relation.relation_type,
            "confidence": relation.confidence
        }
    
    def get_temporal_statistics(self) -> Dict[str, Any]:
        """
        获取时序分析统计信息
        
        Returns:
            时序分析统计信息
        """
        return {
            "agent_name": self.name,
            "temporal_events_count": len(self.temporal_events),
            "temporal_relations_count": len(self.temporal_relations),
            "events_with_timestamps": len([e for e in self.temporal_events if e.timestamp]),
            "event_types_distribution": self._get_event_type_distribution(),
            "temporal_relation_types": self._get_temporal_relation_types()
        }
    
    def _get_event_type_distribution(self) -> Dict[str, int]:
        """获取事件类型分布"""
        distribution = {}
        for event in self.temporal_events:
            event_type = event.event_type
            distribution[event_type] = distribution.get(event_type, 0) + 1
        return distribution
    
    def _get_temporal_relation_types(self) -> Dict[str, int]:
        """获取时序关系类型分布"""
        distribution = {}
        for relation in self.temporal_relations:
            rel_type = relation.relation_type
            distribution[rel_type] = distribution.get(rel_type, 0) + 1
        return distribution 