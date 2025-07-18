#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AutoGen 知识图谱API - 简化版本
专为前端集成优化，暂时使用模拟数据
"""

import uuid
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio
import random

from fastapi import FastAPI, BackgroundTasks, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# ===================== Pydantic 数据模型 =====================

class AnalysisRequest(BaseModel):
    """文本分析请求模型"""
    text: str = Field(..., min_length=1, max_length=50000, description="要分析的文本内容")

class TaskResponse(BaseModel):
    """任务创建响应模型"""
    task_id: str = Field(..., description="唯一任务标识符")
    status: str = Field(..., description="任务状态")
    message: str = Field(..., description="响应消息")
    created_at: str = Field(..., description="任务创建时间")

class StatusResponse(BaseModel):
    """任务状态响应模型"""
    task_id: str = Field(..., description="任务ID")
    status: str = Field(..., description="任务状态: PENDING, PROCESSING, COMPLETED, FAILED")
    progress: Optional[int] = Field(None, ge=0, le=100, description="处理进度百分比")
    message: Optional[str] = Field(None, description="状态描述信息")
    error: Optional[str] = Field(None, description="错误信息（如果失败）")
    started_at: Optional[str] = Field(None, description="处理开始时间")
    completed_at: Optional[str] = Field(None, description="处理完成时间")

class GraphNode(BaseModel):
    """图谱节点模型"""
    id: str = Field(..., description="节点唯一标识符")
    label: str = Field(..., description="节点显示标签")
    size: Optional[float] = Field(1.0, ge=0.1, le=10.0, description="节点大小")
    color: Optional[str] = Field("#4ECDC4", description="节点颜色（十六进制）")
    type: Optional[str] = Field("entity", description="节点类型")
    source_sentence: Optional[str] = Field(None, description="来源句子")

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

class GraphDataResponse(BaseModel):
    """图谱数据响应模型"""
    task_id: str = Field(..., description="任务ID")
    nodes: List[GraphNode] = Field(..., description="图谱节点数组")
    edges: List[GraphEdge] = Field(..., description="图谱边数组")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据信息")

# ===================== 全局状态管理 =====================

class SimpleTaskManager:
    """简化的任务管理器"""
    
    def __init__(self):
        self.tasks: Dict[str, Dict[str, Any]] = {}
    
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
task_manager = SimpleTaskManager()

# ===================== FastAPI 应用初始化 =====================

app = FastAPI(
    title="AutoGen 知识图谱API - 简化版",
    description="专为前端集成优化的知识图谱API",
    version="1.0.0-simple",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===================== 业务逻辑 =====================

def extract_keywords_from_text(text: str) -> List[str]:
    """从文本中提取关键词"""
    import re
    
    # 简单的关键词提取
    words = re.findall(r'\b[\u4e00-\u9fff]{2,}\b|\b[a-zA-Z]{3,}\b', text)
    
    # 过滤停用词
    stop_words = {
        '人工智能', '机器学习', '深度学习', '计算机', '科学', '技术', '系统', '模型', 
        '算法', '数据', '网络', '智能', '自然', '语言', '处理', '视觉', '学习',
        'artificial', 'intelligence', 'machine', 'learning', 'deep', 'computer',
        'science', 'technology', 'system', 'model', 'algorithm', 'data', 'network'
    }
    
    # 基于文本内容智能提取关键词
    if '人工智能' in text or 'AI' in text:
        keywords = ['人工智能', '机器学习', '深度学习', '神经网络', '算法', '数据科学']
    elif '编程' in text or '代码' in text:
        keywords = ['编程', '代码', '软件开发', '算法', '数据结构', '计算机']
    elif '商业' in text or '企业' in text:
        keywords = ['商业', '企业', '管理', '战略', '市场', '客户']
    else:
        # 从文本中提取实际关键词
        unique_words = list(set(words))
        keywords = unique_words[:8]  # 取前8个
    
    # 确保至少有一些关键词
    if len(keywords) < 3:
        keywords.extend(['概念', '要素', '关系'])
    
    return keywords[:10]

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

def assign_cluster_ids(keywords: List[str]) -> Dict[str, str]:
    """基于语义相似性为关键词分配集群ID"""
    clusters = {}
    
    # 预定义的语义集群
    ai_terms = {'人工智能', '机器学习', '深度学习', '神经网络', '算法', 'AI', 'ML', 'DL'}
    tech_terms = {'技术', '系统', '平台', '工具', '软件', '硬件', '计算机', '数据'}
    business_terms = {'企业', '商业', '公司', '管理', '战略', '市场', '客户', '服务'}
    research_terms = {'研究', '科学', '实验', '理论', '方法', '模型', '分析', '测试'}
    
    for keyword in keywords:
        # 根据关键词内容分配集群
        if any(term in keyword for term in ai_terms) or keyword in ai_terms:
            clusters[keyword] = 'cluster_ai'
        elif any(term in keyword for term in tech_terms) or keyword in tech_terms:
            clusters[keyword] = 'cluster_tech'
        elif any(term in keyword for term in business_terms) or keyword in business_terms:
            clusters[keyword] = 'cluster_business'
        elif any(term in keyword for term in research_terms) or keyword in research_terms:
            clusters[keyword] = 'cluster_research'
        elif '开发' in keyword or '编程' in keyword or '代码' in keyword:
            clusters[keyword] = 'cluster_development'
        elif '网络' in keyword or '互联网' in keyword or '通信' in keyword:
            clusters[keyword] = 'cluster_network'
        else:
            # 默认分配到通用集群
            clusters[keyword] = 'cluster_general'
    
    return clusters

def get_cluster_info(cluster_id: str) -> Dict[str, str]:
    """获取集群的显示信息"""
    cluster_info = {
        'cluster_ai': {'name': 'AI技术', 'color': '#FF6B6B'},
        'cluster_tech': {'name': '技术系统', 'color': '#4ECDC4'},
        'cluster_business': {'name': '商业管理', 'color': '#45B7D1'},
        'cluster_research': {'name': '科学研究', 'color': '#96CEB4'},
        'cluster_development': {'name': '软件开发', 'color': '#FFEAA7'},
        'cluster_network': {'name': '网络通信', 'color': '#DDA0DD'},
        'cluster_general': {'name': '通用概念', 'color': '#98D8C8'},
    }
    return cluster_info.get(cluster_id, {'name': cluster_id, 'color': '#A8E6CF'})

def generate_graph_data_from_text(text: str) -> Dict[str, Any]:
    """根据文本生成知识图谱数据（包含集群信息）"""
    keywords = extract_keywords_from_text(text)
    cluster_assignments = assign_cluster_ids(keywords)
    
    nodes = []
    edges = []
    
    # 生成节点（包含clusterId）
    for i, keyword in enumerate(keywords):
        cluster_id = cluster_assignments[keyword]
        cluster_info = get_cluster_info(cluster_id)
        
        node = {
            "id": f"n-{i+1}",
            "label": keyword,
            "size": 1.2 + random.uniform(0.3, 1.8),  # 随机大小
            "color": cluster_info['color'],  # 使用集群颜色
            "type": "concept",
            "clusterId": cluster_id,  # 添加集群ID
            "clusterName": cluster_info['name'],  # 添加集群名称
            "source_sentence": text[:100] + "..." if len(text) > 100 else text
        }
        nodes.append(node)
    
    # 生成边 - 连接相关的概念
    for i in range(len(nodes) - 1):
        if random.random() > 0.3:  # 70%的概率生成连接
            edge = {
                "id": f"e-{len(edges)+1}",
                "source": f"n-{i+1}",
                "target": f"n-{i+2}",
                "label": random.choice(["相关", "包含", "影响", "依赖", "协作"]),
                "size": random.uniform(1.0, 2.5),
                "color": "#00D4FF",
                "type": "relationship",
                "source_sentence": text[:100] + "..." if len(text) > 100 else text
            }
            edges.append(edge)
    
    # 添加一些随机的跨节点连接
    for _ in range(min(3, len(nodes) // 2)):
        if len(nodes) > 2:
            source_idx = random.randint(0, len(nodes) - 1)
            target_idx = random.randint(0, len(nodes) - 1)
            if source_idx != target_idx:
                edge = {
                    "id": f"e-{len(edges)+1}",
                    "source": f"n-{source_idx+1}",
                    "target": f"n-{target_idx+1}",
                    "label": random.choice(["关联", "交互", "支持"]),
                    "size": random.uniform(0.8, 1.5),
                    "color": "#48CAE4",
                    "type": "association"
                }
                edges.append(edge)
    
    # 计算集群统计信息
    cluster_stats = {}
    for node in nodes:
        cluster_id = node['clusterId']
        if cluster_id not in cluster_stats:
            cluster_stats[cluster_id] = {
                'name': node['clusterName'],
                'count': 0,
                'color': node['color']
            }
        cluster_stats[cluster_id]['count'] += 1
    
    return {
        "nodes": nodes,
        "edges": edges,
        "clusters": cluster_stats,  # 添加集群统计信息
        "metadata": {
            "node_count": len(nodes),
            "edge_count": len(edges),
            "cluster_count": len(cluster_stats),  # 添加集群数量
            "text_length": len(text),
            "analysis_duration": round(random.uniform(5.0, 25.0), 1),
            "generated_at": datetime.utcnow().isoformat() + "Z"
        }
    }

async def simulate_text_analysis(task_id: str, text: str):
    """模拟文本分析过程"""
    try:
        # 步骤1: 开始处理
        task_manager.update_task_status(
            task_id,
            status="PROCESSING",
            progress=10,
            message="开始文本分析...",
            started_at=datetime.utcnow().isoformat() + "Z"
        )
        await asyncio.sleep(1)
        
        # 步骤2: 文本预处理
        task_manager.update_task_status(task_id, progress=25, message="正在预处理文本...")
        await asyncio.sleep(1)
        
        # 步骤3: 关键词提取
        task_manager.update_task_status(task_id, progress=50, message="正在提取关键概念...")
        await asyncio.sleep(1)
        
        # 步骤4: 关系分析
        task_manager.update_task_status(task_id, progress=75, message="正在分析概念关系...")
        await asyncio.sleep(1)
        
        # 步骤5: 图谱生成
        task_manager.update_task_status(task_id, progress=90, message="正在生成知识图谱...")
        graph_data = generate_graph_data_from_text(text)
        await asyncio.sleep(0.5)
        
        # 步骤6: 完成
        task_manager.update_task_status(
            task_id,
            status="COMPLETED",
            progress=100,
            message="知识图谱生成完成",
            completed_at=datetime.utcnow().isoformat() + "Z",
            result=graph_data
        )
        
        print(f"[任务 {task_id}] 分析完成 - 生成了 {len(graph_data['nodes'])} 个节点")
        
    except Exception as e:
        print(f"[任务 {task_id}] 处理失败: {str(e)}")
        task_manager.update_task_status(
            task_id,
            status="FAILED",
            message=f"处理失败: {str(e)}",
            error=str(e),
            completed_at=datetime.utcnow().isoformat() + "Z"
        )

# ===================== API 端点 =====================

@app.post("/api/start-analysis", response_model=TaskResponse)
async def start_analysis(request: AnalysisRequest, background_tasks: BackgroundTasks):
    """启动文本分析任务"""
    try:
        # 生成唯一任务ID
        task_id = str(uuid.uuid4())
        
        # 创建任务记录
        task_data = task_manager.create_task(task_id, request.text)
        
        # 添加后台任务
        background_tasks.add_task(simulate_text_analysis, task_id, request.text)
        
        print(f"[API] 创建新任务: {task_id} - 文本长度: {len(request.text)}")
        
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
    """获取任务状态"""
    try:
        # 验证task_id格式
        uuid.UUID(task_id)
        
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
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取任务状态失败: {str(e)}"
        )

@app.get("/api/graph-data/{task_id}", response_model=GraphDataResponse)
async def get_graph_data(task_id: str):
    """获取知识图谱数据"""
    try:
        # 验证task_id格式
        uuid.UUID(task_id)
        
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
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取图谱数据失败: {str(e)}"
        )

# ===================== 健康检查和辅助端点 =====================

@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "AutoGen 知识图谱API服务 - 简化版",
        "version": "1.0.0-simple",
        "status": "running",
        "docs": "/docs"
    }

@app.get("/api/health")
async def health_check():
    """健康检查端点"""
    active_tasks = len([t for t in task_manager.tasks.values() if t["status"] in ["PENDING", "PROCESSING"]])
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "active_tasks": active_tasks,
        "total_tasks": len(task_manager.tasks)
    }

@app.get("/api/tasks")
async def list_tasks():
    """列出所有任务（调试用）"""
    return {
        "tasks": list(task_manager.tasks.keys()),
        "total": len(task_manager.tasks)
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 启动AutoGen知识图谱API服务 (简化版)...")
    print("📖 API文档: http://localhost:8000/docs")
    print("❤️‍🔥 健康检查: http://localhost:8000/api/health")
    uvicorn.run(
        "main_simple:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 