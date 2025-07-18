"""
AutoGen知识图谱生成系统 - FastAPI主应用

提供RESTful API接口，支持知识图谱生成、查询和管理功能。
"""

import logging
import asyncio
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from .models import *
from ..agents import *
from ..tools import GraphDB, TextProcessor, TimeParser
from config import get_settings

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="AutoGen知识图谱生成系统",
    description="基于AutoGen和Neo4j的智能知识图谱生成与查询系统",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境中应该设置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局变量
settings = get_settings()
graph_db = None
text_processor = TextProcessor()
time_parser = TimeParser()
task_store: Dict[str, Dict[str, Any]] = {}  # 简单的内存任务存储


# 依赖注入

async def get_graph_db():
    """获取图数据库连接"""
    global graph_db
    if graph_db is None:
        graph_db = GraphDB(
            uri=settings.neo4j_uri,
            username=settings.neo4j_username,
            password=settings.neo4j_password
        )
    return graph_db


# 异常处理

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """通用异常处理器"""
    logger.error(f"Unexpected error: {exc}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            success=False,
            message="内部服务器错误",
            error=ErrorDetail(
                error_code="INTERNAL_ERROR",
                error_type="ServerError",
                error_message=str(exc)
            )
        ).dict()
    )


# 健康检查

@app.get("/health", response_model=HealthCheck)
async def health_check():
    """系统健康检查"""
    try:
        # 检查数据库连接
        db = await get_graph_db()
        db_status = "healthy" if db.connected else "unhealthy"
        
        return HealthCheck(
            status="healthy",
            version="1.0.0",
            components={
                "database": db_status,
                "text_processor": "healthy",
                "time_parser": "healthy"
            },
            uptime=0.0  # 这里应该计算实际运行时间
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")


# 知识图谱生成

@app.post("/api/v1/knowledge-graph/generate", response_model=TaskResponse)
async def generate_knowledge_graph(
    request: KnowledgeGraphGenerationRequest,
    background_tasks: BackgroundTasks
):
    """生成知识图谱"""
    try:
        # 创建任务ID
        task_id = str(uuid.uuid4())
        
        # 初始化任务状态
        task_store[task_id] = {
            "status": TaskStatus.PENDING,
            "progress": 0.0,
            "created_at": datetime.now(),
            "request": request.dict()
        }
        
        # 添加后台任务
        background_tasks.add_task(
            process_knowledge_graph_generation,
            task_id,
            request
        )
        
        return TaskResponse(
            success=True,
            message="知识图谱生成任务已创建",
            task_id=task_id,
            status=TaskStatus.PENDING,
            progress=0.0
        )
        
    except Exception as e:
        logger.error(f"Failed to create knowledge graph generation task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def process_knowledge_graph_generation(task_id: str, request: KnowledgeGraphGenerationRequest):
    """处理知识图谱生成任务"""
    try:
        # 更新任务状态
        task_store[task_id]["status"] = TaskStatus.RUNNING
        task_store[task_id]["progress"] = 0.1
        
        # 获取文本输入
        text_input = request.text_input.text
        
        # 1. 文本解构
        logger.info(f"Task {task_id}: Starting text deconstruction...")
        text_agent = TextDeconstructionAgent()
        text_data = text_agent.deconstruct_text(text_input)
        task_store[task_id]["progress"] = 0.2
        
        # 2. 实体关系抽取
        logger.info(f"Task {task_id}: Starting entity-relation extraction...")
        ece_agent = ECEAgent()
        extraction_data = ece_agent.extract_entities_relations(text_data)
        task_store[task_id]["progress"] = 0.4
        
        # 3. 关系增强
        logger.info(f"Task {task_id}: Starting relation enhancement...")
        ree_agent = REEAgent()
        enhancement_data = ree_agent.enhance_relations(extraction_data)
        task_store[task_id]["progress"] = 0.6
        
        # 4. 时序分析
        logger.info(f"Task {task_id}: Starting temporal analysis...")
        temporal_agent = TemporalAnalystAgent()
        temporal_data = temporal_agent.analyze_temporal_information(extraction_data)
        task_store[task_id]["progress"] = 0.8
        
        # 5. 图谱合成
        logger.info(f"Task {task_id}: Starting graph synthesis...")
        synthesis_agent = GraphSynthesisAgent()
        agent_outputs = {
            "text_deconstruction": text_data,
            "entity_relation_extraction": extraction_data,
            "relation_enhancement": enhancement_data,
            "temporal_analysis": temporal_data
        }
        knowledge_graph = synthesis_agent.synthesize_knowledge_graph(agent_outputs)
        task_store[task_id]["progress"] = 0.9
        
        # 6. 保存到数据库
        if request.save_to_db:
            logger.info(f"Task {task_id}: Saving to database...")
            db = await get_graph_db()
            if db.connected:
                success = db.import_knowledge_graph(knowledge_graph)
                if not success:
                    logger.warning(f"Task {task_id}: Failed to save to database")
        
        # 完成任务
        task_store[task_id]["status"] = TaskStatus.COMPLETED
        task_store[task_id]["progress"] = 1.0
        task_store[task_id]["result"] = {
            "graph_id": str(uuid.uuid4()),
            "nodes_count": len(knowledge_graph.get("nodes", [])),
            "edges_count": len(knowledge_graph.get("edges", [])),
            "knowledge_graph": knowledge_graph
        }
        task_store[task_id]["completed_at"] = datetime.now()
        
        logger.info(f"Task {task_id}: Knowledge graph generation completed successfully")
        
    except Exception as e:
        logger.error(f"Task {task_id}: Failed to generate knowledge graph: {e}")
        task_store[task_id]["status"] = TaskStatus.FAILED
        task_store[task_id]["error"] = str(e)


@app.get("/api/v1/tasks/{task_id}", response_model=TaskResponse)
async def get_task_status(task_id: str):
    """获取任务状态"""
    if task_id not in task_store:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = task_store[task_id]
    
    return TaskResponse(
        success=True,
        message="任务状态获取成功",
        task_id=task_id,
        status=task["status"],
        progress=task.get("progress"),
        result=task.get("result"),
        error=task.get("error")
    )


# 问答系统

@app.post("/api/v1/qa/ask", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest, db: GraphDB = Depends(get_graph_db)):
    """问答接口"""
    try:
        # 创建问答智能体
        qa_agent = QAAgent()
        
        # 加载知识图谱（这里简化处理，实际应该根据graph_id加载）
        if db.connected:
            knowledge_graph = db.export_knowledge_graph()
            qa_agent.load_knowledge_graph(knowledge_graph)
        
        # 处理问题
        result = qa_agent.answer_question(request.question)
        
        return QuestionResponse(
            success=True,
            message="问题处理成功",
            question_id=result["question"]["id"],
            answer=result["answer"]["answer_text"],
            confidence=result["answer"]["confidence"],
            supporting_evidence=result["answer"]["supporting_evidence"],
            cypher_query=result["answer"]["cypher_query"],
            reasoning_steps=result["answer"]["reasoning_steps"]
        )
        
    except Exception as e:
        logger.error(f"Failed to process question: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 图谱查询

@app.post("/api/v1/graph/query", response_model=GraphQueryResponse)
async def query_graph(request: GraphQueryRequest, db: GraphDB = Depends(get_graph_db)):
    """执行图谱查询"""
    try:
        start_time = datetime.now()
        
        # 执行查询
        results = db.execute_query(request.cypher_query, request.parameters)
        
        # 限制结果数量
        if len(results) > request.limit:
            results = results[:request.limit]
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return GraphQueryResponse(
            success=True,
            message="查询执行成功",
            query=request.cypher_query,
            results=results,
            count=len(results),
            execution_time=execution_time
        )
        
    except Exception as e:
        logger.error(f"Failed to execute graph query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 图谱管理

@app.get("/api/v1/graph/statistics", response_model=Dict[str, Any])
async def get_graph_statistics(db: GraphDB = Depends(get_graph_db)):
    """获取图谱统计信息"""
    try:
        statistics = db.get_graph_statistics()
        return {
            "success": True,
            "message": "统计信息获取成功",
            "data": statistics
        }
    except Exception as e:
        logger.error(f"Failed to get graph statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/graph/export")
async def export_graph(
    format: ExportFormat = Query(ExportFormat.JSON, description="导出格式"),
    db: GraphDB = Depends(get_graph_db)
):
    """导出知识图谱"""
    try:
        if format == ExportFormat.JSON:
            knowledge_graph = db.export_knowledge_graph()
            return knowledge_graph
        elif format == ExportFormat.CYPHER:
            knowledge_graph = db.export_knowledge_graph()
            # 这里应该转换为Cypher格式
            return {"message": "Cypher export not implemented yet"}
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")
            
    except Exception as e:
        logger.error(f"Failed to export graph: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 文本处理工具

@app.post("/api/v1/tools/text/analyze")
async def analyze_text(text: str):
    """文本分析接口"""
    try:
        # 文本统计
        statistics = text_processor.get_text_statistics(text)
        
        # 关键词提取
        keywords = text_processor.extract_keywords(text)
        
        # 实体识别（简单版本）
        entities = text_processor.extract_entities_simple(text)
        
        return {
            "success": True,
            "message": "文本分析完成",
            "data": {
                "statistics": statistics,
                "keywords": keywords,
                "entities": entities
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to analyze text: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/tools/time/parse")
async def parse_time_expressions(text: str):
    """时间表达式解析接口"""
    try:
        expressions = time_parser.parse_time_expressions(text)
        statistics = time_parser.get_time_statistics(expressions)
        
        return {
            "success": True,
            "message": "时间解析完成",
            "data": {
                "expressions": [
                    {
                        "original_text": expr.original_text,
                        "normalized_text": expr.normalized_text,
                        "time_type": expr.time_type,
                        "parsed_datetime": expr.parsed_datetime.isoformat() if expr.parsed_datetime else None,
                        "confidence": expr.confidence
                    }
                    for expr in expressions
                ],
                "statistics": statistics
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to parse time expressions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 系统管理

@app.delete("/api/v1/graph/clear")
async def clear_graph(db: GraphDB = Depends(get_graph_db)):
    """清空图谱数据"""
    try:
        success = db.clear_database()
        if success:
            return {
                "success": True,
                "message": "图谱数据已清空"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to clear database")
            
    except Exception as e:
        logger.error(f"Failed to clear graph: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/tasks", response_model=List[Dict[str, Any]])
async def list_tasks(
    status: Optional[TaskStatus] = Query(None, description="按状态过滤"),
    limit: int = Query(20, description="结果限制", ge=1, le=100)
):
    """获取任务列表"""
    try:
        tasks = []
        for task_id, task_data in task_store.items():
            if status is None or task_data["status"] == status:
                tasks.append({
                    "task_id": task_id,
                    "status": task_data["status"],
                    "progress": task_data.get("progress", 0.0),
                    "created_at": task_data["created_at"],
                    "completed_at": task_data.get("completed_at")
                })
        
        # 按创建时间排序并限制数量
        tasks.sort(key=lambda x: x["created_at"], reverse=True)
        tasks = tasks[:limit]
        
        return tasks
        
    except Exception as e:
        logger.error(f"Failed to list tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 启动配置

def create_app():
    """创建应用实例"""
    return app


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 