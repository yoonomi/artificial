"""
API数据模型定义

定义了用于Web API的Pydantic数据模型，包括请求和响应模型。
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum


class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentType(str, Enum):
    """智能体类型枚举"""
    CHIEF_ONTOLOGIST = "chief_ontologist"
    TEXT_DECONSTRUCTION = "text_deconstruction"
    ENTITY_RELATION_EXTRACTION = "entity_relation_extraction"
    RELATION_ENHANCEMENT = "relation_enhancement"
    TEMPORAL_ANALYSIS = "temporal_analysis"
    GRAPH_SYNTHESIS = "graph_synthesis"
    QA = "qa"


# 请求模型

class TextInput(BaseModel):
    """文本输入模型"""
    text: str = Field(..., description="输入文本内容", min_length=1, max_length=50000)
    title: Optional[str] = Field(None, description="文档标题")
    source: Optional[str] = Field(None, description="文档来源")
    metadata: Optional[Dict[str, Any]] = Field(None, description="额外元数据")


class KnowledgeGraphGenerationRequest(BaseModel):
    """知识图谱生成请求模型"""
    text_input: TextInput = Field(..., description="文本输入")
    config: Optional[Dict[str, Any]] = Field(None, description="生成配置")
    agents_to_run: Optional[List[AgentType]] = Field(None, description="要运行的智能体列表")
    save_to_db: bool = Field(True, description="是否保存到数据库")


class QuestionRequest(BaseModel):
    """问答请求模型"""
    question: str = Field(..., description="问题文本", min_length=1, max_length=1000)
    knowledge_graph_id: Optional[str] = Field(None, description="知识图谱ID")
    context: Optional[Dict[str, Any]] = Field(None, description="额外上下文")


class GraphQueryRequest(BaseModel):
    """图谱查询请求模型"""
    cypher_query: str = Field(..., description="Cypher查询语句")
    parameters: Optional[Dict[str, Any]] = Field(None, description="查询参数")
    limit: int = Field(100, description="结果限制", ge=1, le=1000)


# 响应模型

class BaseResponse(BaseModel):
    """基础响应模型"""
    success: bool = Field(..., description="操作是否成功")
    message: str = Field(..., description="响应消息")
    timestamp: datetime = Field(default_factory=datetime.now, description="响应时间戳")


class TaskResponse(BaseResponse):
    """任务响应模型"""
    task_id: str = Field(..., description="任务ID")
    status: TaskStatus = Field(..., description="任务状态")
    progress: Optional[float] = Field(None, description="任务进度 (0-1)")
    result: Optional[Dict[str, Any]] = Field(None, description="任务结果")
    error: Optional[str] = Field(None, description="错误信息")


class KnowledgeGraphResponse(BaseResponse):
    """知识图谱响应模型"""
    graph_id: str = Field(..., description="图谱ID")
    nodes: List[Dict[str, Any]] = Field(..., description="节点列表")
    edges: List[Dict[str, Any]] = Field(..., description="边列表")
    metadata: Dict[str, Any] = Field(..., description="图谱元数据")
    statistics: Dict[str, Any] = Field(..., description="图谱统计信息")


class QuestionResponse(BaseResponse):
    """问答响应模型"""
    question_id: str = Field(..., description="问题ID")
    answer: str = Field(..., description="答案文本")
    confidence: float = Field(..., description="置信度", ge=0, le=1)
    supporting_evidence: List[Dict[str, Any]] = Field(..., description="支撑证据")
    cypher_query: str = Field(..., description="生成的查询语句")
    reasoning_steps: List[str] = Field(..., description="推理步骤")


class GraphQueryResponse(BaseResponse):
    """图谱查询响应模型"""
    query: str = Field(..., description="执行的查询")
    results: List[Dict[str, Any]] = Field(..., description="查询结果")
    count: int = Field(..., description="结果数量")
    execution_time: float = Field(..., description="执行时间(秒)")


# 实体和关系模型

class EntityModel(BaseModel):
    """实体模型"""
    id: str = Field(..., description="实体ID")
    text: str = Field(..., description="实体文本")
    type: str = Field(..., description="实体类型")
    start_pos: Optional[int] = Field(None, description="起始位置")
    end_pos: Optional[int] = Field(None, description="结束位置")
    confidence: float = Field(..., description="置信度", ge=0, le=1)
    attributes: Optional[Dict[str, Any]] = Field(None, description="实体属性")


class RelationModel(BaseModel):
    """关系模型"""
    id: str = Field(..., description="关系ID")
    subject: str = Field(..., description="主语实体ID")
    predicate: str = Field(..., description="谓语关系类型")
    object: str = Field(..., description="宾语实体ID")
    confidence: float = Field(..., description="置信度", ge=0, le=1)
    context: Optional[str] = Field(None, description="关系上下文")
    attributes: Optional[Dict[str, Any]] = Field(None, description="关系属性")


class TemporalEventModel(BaseModel):
    """时序事件模型"""
    id: str = Field(..., description="事件ID")
    event_text: str = Field(..., description="事件文本")
    timestamp: Optional[datetime] = Field(None, description="事件时间戳")
    time_expression: str = Field(..., description="时间表达式")
    event_type: str = Field(..., description="事件类型")
    entities_involved: List[str] = Field(..., description="涉及的实体ID列表")
    confidence: float = Field(..., description="置信度", ge=0, le=1)


# 配置模型

class AgentConfig(BaseModel):
    """智能体配置模型"""
    name: str = Field(..., description="智能体名称")
    enabled: bool = Field(True, description="是否启用")
    config: Optional[Dict[str, Any]] = Field(None, description="智能体特定配置")


class SystemConfig(BaseModel):
    """系统配置模型"""
    agents: List[AgentConfig] = Field(..., description="智能体配置列表")
    database: Dict[str, Any] = Field(..., description="数据库配置")
    logging: Dict[str, Any] = Field(..., description="日志配置")
    api: Dict[str, Any] = Field(..., description="API配置")


# 统计和分析模型

class TextStatistics(BaseModel):
    """文本统计模型"""
    total_length: int = Field(..., description="总长度")
    word_count: int = Field(..., description="词数")
    sentence_count: int = Field(..., description="句子数")
    language: str = Field(..., description="语言")
    character_count: Dict[str, int] = Field(..., description="字符统计")


class GraphStatistics(BaseModel):
    """图谱统计模型"""
    node_count: int = Field(..., description="节点数量")
    edge_count: int = Field(..., description="边数量")
    node_types: Dict[str, int] = Field(..., description="节点类型分布")
    edge_types: Dict[str, int] = Field(..., description="边类型分布")
    graph_density: float = Field(..., description="图密度")
    average_degree: float = Field(..., description="平均度数")


class ProcessingStatistics(BaseModel):
    """处理统计模型"""
    processing_time: float = Field(..., description="处理时间(秒)")
    agent_statistics: Dict[str, Dict[str, Any]] = Field(..., description="智能体统计")
    text_statistics: TextStatistics = Field(..., description="文本统计")
    graph_statistics: GraphStatistics = Field(..., description="图谱统计")


# 错误模型

class ErrorDetail(BaseModel):
    """错误详情模型"""
    error_code: str = Field(..., description="错误代码")
    error_type: str = Field(..., description="错误类型")
    error_message: str = Field(..., description="错误消息")
    details: Optional[Dict[str, Any]] = Field(None, description="详细信息")
    suggestions: Optional[List[str]] = Field(None, description="解决建议")


class ErrorResponse(BaseResponse):
    """错误响应模型"""
    error: ErrorDetail = Field(..., description="错误详情")


# 分页模型

class PaginationParams(BaseModel):
    """分页参数模型"""
    page: int = Field(1, description="页码", ge=1)
    page_size: int = Field(20, description="每页大小", ge=1, le=100)


class PaginatedResponse(BaseModel):
    """分页响应模型"""
    items: List[Any] = Field(..., description="数据项")
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页大小")
    total_pages: int = Field(..., description="总页数")
    has_next: bool = Field(..., description="是否有下一页")
    has_prev: bool = Field(..., description="是否有上一页")


# 健康检查模型

class HealthCheck(BaseModel):
    """健康检查模型"""
    status: str = Field(..., description="系统状态")
    version: str = Field(..., description="系统版本")
    timestamp: datetime = Field(default_factory=datetime.now, description="检查时间")
    components: Dict[str, str] = Field(..., description="组件状态")
    uptime: float = Field(..., description="运行时间(秒)")


# 批处理模型

class BatchProcessingRequest(BaseModel):
    """批处理请求模型"""
    texts: List[TextInput] = Field(..., description="文本输入列表", max_items=100)
    config: Optional[Dict[str, Any]] = Field(None, description="批处理配置")
    async_mode: bool = Field(True, description="是否异步处理")


class BatchProcessingResponse(BaseResponse):
    """批处理响应模型"""
    batch_id: str = Field(..., description="批处理ID")
    total_items: int = Field(..., description="总项目数")
    processed_items: int = Field(..., description="已处理项目数")
    failed_items: int = Field(..., description="失败项目数")
    results: List[Dict[str, Any]] = Field(..., description="处理结果列表")
    processing_time: float = Field(..., description="总处理时间")


# 导出模型

class ExportFormat(str, Enum):
    """导出格式枚举"""
    JSON = "json"
    CSV = "csv"
    CYPHER = "cypher"
    GEXF = "gexf"
    GRAPHML = "graphml"


class ExportRequest(BaseModel):
    """导出请求模型"""
    knowledge_graph_id: str = Field(..., description="知识图谱ID")
    format: ExportFormat = Field(..., description="导出格式")
    options: Optional[Dict[str, Any]] = Field(None, description="导出选项")


class ExportResponse(BaseResponse):
    """导出响应模型"""
    download_url: str = Field(..., description="下载链接")
    file_size: int = Field(..., description="文件大小(字节)")
    format: str = Field(..., description="文件格式")
    expires_at: datetime = Field(..., description="链接过期时间") 