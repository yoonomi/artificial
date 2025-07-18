"""
AutoGen知识图谱生成系统 - FastAPI主应用

提供RESTful API接口，支持知识图谱生成、查询和管理功能。
"""

import os
import sys
import uuid
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor

from fastapi import FastAPI, BackgroundTasks, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.text_deconstruction_agent import create_text_deconstruction_agent
from agents.chief_ontologist import create_chief_ontologist
from agents.ece_agent import create_ece_agent
from agents.ree_agent import create_ree_agent
from agents.graph_synthesis_agent import create_graph_synthesis_agent
from tools.graph_db import Neo4jManager

# ===================== Pydantic 数据模型 =====================

class AnalysisRequest(BaseModel):
    """文本分析请求模型"""
    text: str = Field(..., min_length=1, max_length=50000, description="要分析的文本内容")
    
    class Config:
        schema_extra = {
            "example": {
                "text": "人工智能是计算机科学的一个分支，旨在创建能够执行通常需要人类智能的任务的系统。"
            }
        }

class TaskResponse(BaseModel):
    """任务创建响应模型"""
    task_id: str = Field(..., description="唯一任务标识符")
    status: str = Field(..., description="任务状态")
    message: str = Field(..., description="响应消息")
    created_at: str = Field(..., description="任务创建时间")
    
    class Config:
        schema_extra = {
            "example": {
                "task_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "PENDING",
                "message": "任务已创建，正在排队处理",
                "created_at": "2024-01-20T10:30:00Z"
            }
        }

class StatusResponse(BaseModel):
    """任务状态响应模型"""
    task_id: str = Field(..., description="任务ID")
    status: str = Field(..., description="任务状态: PENDING, PROCESSING, COMPLETED, FAILED")
    progress: Optional[int] = Field(None, ge=0, le=100, description="处理进度百分比")
    message: Optional[str] = Field(None, description="状态描述信息")
    error: Optional[str] = Field(None, description="错误信息（如果失败）")
    started_at: Optional[str] = Field(None, description="处理开始时间")
    completed_at: Optional[str] = Field(None, description="处理完成时间")
    
    class Config:
        schema_extra = {
            "example": {
                "task_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "COMPLETED",
                "progress": 100,
                "message": "知识图谱构建完成",
                "started_at": "2024-01-20T10:30:05Z",
                "completed_at": "2024-01-20T10:30:45Z"
            }
        }

class GraphNode(BaseModel):
    """图谱节点模型"""
    id: str = Field(..., description="节点唯一标识符")
    label: str = Field(..., description="节点显示标签")
    size: Optional[float] = Field(1.0, ge=0.1, le=10.0, description="节点大小")
    color: Optional[str] = Field("#4ECDC4", description="节点颜色（十六进制）")
    type: Optional[str] = Field("entity", description="节点类型")
    source_sentence: Optional[str] = Field(None, description="来源句子")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "n-1",
                "label": "人工智能",
                "size": 2.5,
                "color": "#FF6B6B",
                "type": "concept",
                "source_sentence": "人工智能是计算机科学的一个分支。"
            }
        }

class GraphEdge(BaseModel):
    """图谱边模型"""
    id: str = Field(..., description="边唯一标识符")
    source: str = Field(..., description="源节点ID")
    target: str = Field(..., description="目标节点ID")
    label: str = Field(..., description="关系标签")
    size: Optional[float] = Field(1.0, ge=0.1, le=5.0, description="边粗细")
    color: Optional[str] = Field("#00D4FF", description="边颜色（十六进制）")
    type: Optional[str] = Field("relationship", description="关系类型")
    source_sentence: Optional[str] = Field(None, description="来源句子")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "e-1",
                "source": "n-1",
                "target": "n-2",
                "label": "包含",
                "size": 2.0,
                "color": "#00D4FF",
                "type": "contains",
                "source_sentence": "人工智能包含机器学习等多个子领域。"
            }
        }

class GraphDataResponse(BaseModel):
    """图谱数据响应模型"""
    task_id: str = Field(..., description="任务ID")
    nodes: List[GraphNode] = Field(..., description="图谱节点数组")
    edges: List[GraphEdge] = Field(..., description="图谱边数组")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据信息")
    
    class Config:
        schema_extra = {
            "example": {
                "task_id": "550e8400-e29b-41d4-a716-446655440000",
                "nodes": [
                    {
                        "id": "n-1",
                        "label": "人工智能",
                        "size": 2.5,
                        "color": "#FF6B6B"
                    }
                ],
                "edges": [
                    {
                        "id": "e-1",
                        "source": "n-1",
                        "target": "n-2",
                        "label": "包含"
                    }
                ],
                "metadata": {
                    "node_count": 15,
                    "edge_count": 22,
                    "analysis_duration": 42.5
                }
            }
        }

# ===================== 全局状态管理 =====================

class TaskManager:
    """任务管理器"""
    
    def __init__(self):
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    def create_task(self, task_id: str, text: str) -> Dict[str, Any]:
        """创建新任务"""
        task_data = {
            "task_id": task_id,
            "text": text,
            "status": "PENDING",
            "progress": 0,
            "message": "任务已创建，正在排队处理",
            "created_at": datetime.utcnow().isoformat() + "Z",
            "started_at": None,
            "completed_at": None,
            "error": None,
            "result": None
        }
        self.tasks[task_id] = task_data
        return task_data
    
    def update_task_status(self, task_id: str, **updates):
        """更新任务状态"""
        if task_id in self.tasks:
            self.tasks[task_id].update(updates)
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务信息"""
        return self.tasks.get(task_id)
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        task = self.get_task(task_id)
        if not task:
            return None
        
        return {
            "task_id": task_id,
            "status": task["status"],
            "progress": task["progress"],
            "message": task["message"],
            "error": task["error"],
            "started_at": task["started_at"],
            "completed_at": task["completed_at"]
        }
    
    def get_graph_data(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取图谱数据"""
        task = self.get_task(task_id)
        if not task or task["status"] != "COMPLETED" or not task["result"]:
            return None
        
        return {
            "task_id": task_id,
            "nodes": task["result"].get("nodes", []),
            "edges": task["result"].get("edges", []),
            "metadata": task["result"].get("metadata", {})
        }

# 全局任务管理器实例
task_manager = TaskManager()

# ===================== FastAPI 应用初始化 =====================

app = FastAPI(
    title="AutoGen 知识图谱API",
    description="基于多智能体的知识图谱构建系统API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===================== 核心业务逻辑 =====================

async def process_text_analysis(task_id: str, text: str):
    """
    异步处理文本分析任务
    """
    try:
        # 更新任务状态为处理中
        task_manager.update_task_status(
            task_id,
            status="PROCESSING",
            progress=10,
            message="开始文本分析...",
            started_at=datetime.utcnow().isoformat() + "Z"
        )
        
        print(f"[任务 {task_id}] 开始处理文本分析...")
        
        # 步骤1: 文本解构
        task_manager.update_task_status(task_id, progress=20, message="正在解构文本...")
        text_agent = create_text_deconstruction_agent()
        
        # 步骤2: 本体定义
        task_manager.update_task_status(task_id, progress=30, message="正在定义本体结构...")
        ontologist = create_chief_ontologist()
        
        # 步骤3: 实体抽取
        task_manager.update_task_status(task_id, progress=50, message="正在抽取实体...")
        ece_agent = create_ece_agent()
        
        # 步骤4: 关系抽取
        task_manager.update_task_status(task_id, progress=70, message="正在抽取关系...")
        ree_agent = create_ree_agent()
        
        # 步骤5: 图谱合成
        task_manager.update_task_status(task_id, progress=85, message="正在合成知识图谱...")
        synthesis_agent = create_graph_synthesis_agent()
        
        # 模拟实际处理（这里可以集成真实的AutoGen流程）
        await asyncio.sleep(2)  # 模拟处理时间
        
        # 生成模拟的图谱数据
        graph_data = generate_sample_graph_data(text)
        
        # 步骤6: 完成处理
        task_manager.update_task_status(
            task_id,
            status="COMPLETED",
            progress=100,
            message="知识图谱构建完成",
            completed_at=datetime.utcnow().isoformat() + "Z",
            result=graph_data
        )
        
        print(f"[任务 {task_id}] 处理完成")
        
    except Exception as e:
        print(f"[任务 {task_id}] 处理失败: {str(e)}")
        task_manager.update_task_status(
            task_id,
            status="FAILED",
            message=f"处理失败: {str(e)}",
            error=str(e),
            completed_at=datetime.utcnow().isoformat() + "Z"
        )

def generate_sample_graph_data(text: str) -> Dict[str, Any]:
    """
    根据输入文本生成示例图谱数据
    实际应用中，这里应该调用真实的AutoGen分析流程
    """
    # 基于文本内容生成相关的节点
    keywords = extract_keywords_from_text(text)
    
    nodes = []
    edges = []
    
    # 生成节点
    for i, keyword in enumerate(keywords[:10]):  # 限制最多10个节点
        node = {
            "id": f"n-{i+1}",
            "label": keyword,
            "size": 1.5 + (len(keyword) / 10),  # 基于关键词长度调整大小
            "color": get_color_for_keyword(keyword),
            "type": "entity",
            "source_sentence": text[:100] + "..." if len(text) > 100 else text
        }
        nodes.append(node)
    
    # 生成边（连接前几个节点）
    for i in range(min(5, len(nodes) - 1)):
        edge = {
            "id": f"e-{i+1}",
            "source": f"n-{i+1}",
            "target": f"n-{i+2}",
            "label": "相关",
            "size": 1.5,
            "color": "#00D4FF",
            "type": "relationship",
            "source_sentence": text[:100] + "..." if len(text) > 100 else text
        }
        edges.append(edge)
    
    # 添加一些随机连接
    import random
    for _ in range(min(3, len(nodes) // 2)):
        if len(nodes) > 2:
            source_idx = random.randint(0, len(nodes) - 1)
            target_idx = random.randint(0, len(nodes) - 1)
            if source_idx != target_idx:
                edge = {
                    "id": f"e-random-{len(edges)+1}",
                    "source": f"n-{source_idx+1}",
                    "target": f"n-{target_idx+1}",
                    "label": "关联",
                    "size": 1.0,
                    "color": "#48CAE4",
                    "type": "association"
                }
                edges.append(edge)
    
    return {
        "nodes": nodes,
        "edges": edges,
        "metadata": {
            "node_count": len(nodes),
            "edge_count": len(edges),
            "text_length": len(text),
            "analysis_duration": 15.5,
            "generated_at": datetime.utcnow().isoformat() + "Z"
        }
    }

def extract_keywords_from_text(text: str) -> List[str]:
    """从文本中提取关键词"""
    # 简单的关键词提取（实际应用中应使用更复杂的NLP技术）
    import re
    
    # 移除标点符号并分词
    words = re.findall(r'\b[\u4e00-\u9fff]+\b|\b[a-zA-Z]+\b', text)
    
    # 过滤短词和常见停用词
    stop_words = {'的', '是', '在', '有', '和', '与', '或', '但', '然而', '因此', '所以', 
                  'the', 'is', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for'}
    
    keywords = [word for word in words if len(word) > 1 and word.lower() not in stop_words]
    
    # 去重并保持原顺序
    seen = set()
    unique_keywords = []
    for keyword in keywords:
        if keyword not in seen:
            seen.add(keyword)
            unique_keywords.append(keyword)
    
    return unique_keywords[:15]  # 返回前15个关键词

def get_color_for_keyword(keyword: str) -> str:
    """为关键词生成颜色"""
    colors = [
        "#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7",
        "#DDA0DD", "#98D8C8", "#A8E6CF", "#FFB6C1", "#87CEEB",
        "#F0E68C", "#E6E6FA", "#FFA07A", "#20B2AA", "#DAA520"
    ]
    # 基于关键词的哈希值选择颜色
    import hashlib
    hash_value = int(hashlib.md5(keyword.encode()).hexdigest(), 16)
    return colors[hash_value % len(colors)]

# ===================== API 端点 =====================

@app.post("/api/start-analysis", response_model=TaskResponse)
async def start_analysis(request: AnalysisRequest, background_tasks: BackgroundTasks):
    """
    启动文本分析任务
    """
    try:
        # 生成唯一任务ID
        task_id = str(uuid.uuid4())
        
        # 创建任务记录
        task_data = task_manager.create_task(task_id, request.text)
        
        # 添加后台任务
        background_tasks.add_task(process_text_analysis, task_id, request.text)
        
        return TaskResponse(
            task_id=task_id,
            status="PENDING",
            message="任务已创建，正在排队处理",
            created_at=task_data["created_at"]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建任务失败: {str(e)}"
        )

@app.get("/api/analysis-status/{task_id}", response_model=StatusResponse)
async def get_analysis_status(task_id: str):
    """
    获取任务状态
    """
    try:
        # 验证task_id格式
        uuid.UUID(task_id)  # 验证是否为有效UUID
        
        task_status = task_manager.get_task_status(task_id)
        
        if not task_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"任务ID {task_id} 不存在"
            )
        
        return StatusResponse(**task_status)
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的任务ID格式"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取任务状态失败: {str(e)}"
        )

@app.get("/api/graph-data/{task_id}", response_model=GraphDataResponse)
async def get_graph_data(task_id: str):
    """
    获取知识图谱数据
    """
    try:
        # 验证task_id格式
        uuid.UUID(task_id)  # 验证是否为有效UUID
        
        graph_data = task_manager.get_graph_data(task_id)
        
        if not graph_data:
            task = task_manager.get_task(task_id)
            if not task:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"任务ID {task_id} 不存在"
                )
            elif task["status"] != "COMPLETED":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"任务尚未完成，当前状态: {task['status']}"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="图谱数据不可用"
                )
        
        return GraphDataResponse(**graph_data)
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的任务ID格式"
        )
    except HTTPException:
        raise  # 重新抛出HTTP异常
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取图谱数据失败: {str(e)}"
        )

# ===================== 健康检查和信息端点 =====================

@app.get("/")
async def root():
    """根路径，返回API信息"""
    return {
        "message": "AutoGen 知识图谱API服务",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/api/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "active_tasks": len([t for t in task_manager.tasks.values() if t["status"] in ["PENDING", "PROCESSING"]]),
        "total_tasks": len(task_manager.tasks)
    }

@app.get("/api/tasks")
async def list_tasks():
    """列出所有任务（调试用）"""
    return {
        "tasks": list(task_manager.tasks.keys()),
        "total": len(task_manager.tasks)
    }

# ===================== 异常处理 =====================

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理器"""
    return {
        "error": "内部服务器错误",
        "detail": str(exc),
        "path": str(request.url)
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 启动AutoGen知识图谱API服务...")
    print("📖 API文档: http://localhost:8000/docs")
    print("🔍 ReDoc文档: http://localhost:8000/redoc")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 