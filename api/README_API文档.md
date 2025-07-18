# AutoGen 知识图谱API 后端文档

## 🎯 概述

AutoGen 知识图谱API是一个基于FastAPI构建的现代化后端服务，支持异步任务处理的知识图谱构建和查询系统。该API设计用于支持双栏布局的前端应用，用户可以在左侧输入文本，右侧实时展示生成的3D知识图谱。

## 🚀 核心特性

### ✨ 异步任务处理
- **非阻塞设计**: 文本分析任务在后台异步执行
- **实时状态跟踪**: 通过WebSocket或轮询获取任务进度
- **任务队列管理**: 支持多个并发分析任务

### 🔄 三个核心端点
1. **启动分析** - 接收文本，立即返回任务ID
2. **状态查询** - 实时监控任务执行状态和进度
3. **数据获取** - 返回Reagraph兼容的图谱数据

### 📊 数据格式兼容
- **前端适配**: 直接适配Reagraph组件格式
- **结构化输出**: 标准化的nodes和edges数组
- **元数据支持**: 包含丰富的分析元信息

## 🔧 技术架构

```
FastAPI Application
├── 路由层 (API Endpoints)
├── 业务逻辑层 (Text Analysis)
├── 任务管理层 (Task Manager)
├── 数据模型层 (Pydantic Models)
└── 异常处理层 (Error Handling)
```

## 📡 API端点详述

### 1. POST `/api/start-analysis`

**功能**: 启动文本分析任务

**请求格式**:
```json
{
  "text": "人工智能是计算机科学的一个分支，旨在创建能够执行通常需要人类智能的任务的系统。"
}
```

**响应格式**:
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "PENDING",
  "message": "任务已创建，正在排队处理",
  "created_at": "2024-01-20T10:30:00Z"
}
```

**cURL示例**:
```bash
curl -X POST "http://localhost:8000/api/start-analysis" \
     -H "Content-Type: application/json" \
     -d '{"text": "您的文本内容"}'
```

**Python示例**:
```python
import requests

response = requests.post(
    "http://localhost:8000/api/start-analysis",
    json={"text": "人工智能相关文本..."}
)
data = response.json()
task_id = data["task_id"]
```

### 2. GET `/api/analysis-status/{task_id}`

**功能**: 获取任务执行状态

**URL参数**:
- `task_id`: 任务唯一标识符 (UUID格式)

**响应格式**:
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "PROCESSING", 
  "progress": 75,
  "message": "正在抽取关系...",
  "error": null,
  "started_at": "2024-01-20T10:30:05Z",
  "completed_at": null
}
```

**状态值说明**:
- `PENDING`: 任务已创建，等待处理
- `PROCESSING`: 任务正在执行中
- `COMPLETED`: 任务已完成
- `FAILED`: 任务执行失败

**轮询示例**:
```python
import time
import requests

def wait_for_completion(task_id, max_wait=300):
    """等待任务完成，最长等待5分钟"""
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        response = requests.get(f"http://localhost:8000/api/analysis-status/{task_id}")
        data = response.json()
        
        status = data["status"]
        print(f"状态: {status} ({data.get('progress', 0)}%)")
        
        if status == "COMPLETED":
            return True
        elif status == "FAILED":
            print(f"任务失败: {data.get('error')}")
            return False
        
        time.sleep(2)  # 每2秒轮询一次
    
    print("任务超时")
    return False
```

### 3. GET `/api/graph-data/{task_id}`

**功能**: 获取生成的知识图谱数据

**URL参数**:
- `task_id`: 已完成任务的ID

**响应格式**:
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "nodes": [
    {
      "id": "n-1",
      "label": "人工智能",
      "size": 2.5,
      "color": "#FF6B6B",
      "type": "concept",
      "source_sentence": "人工智能是计算机科学的一个分支。"
    }
  ],
  "edges": [
    {
      "id": "e-1",
      "source": "n-1",
      "target": "n-2", 
      "label": "包含",
      "size": 2.0,
      "color": "#00D4FF",
      "type": "contains",
      "source_sentence": "人工智能包含机器学习等多个子领域。"
    }
  ],
  "metadata": {
    "node_count": 15,
    "edge_count": 22,
    "analysis_duration": 42.5,
    "text_length": 1250,
    "generated_at": "2024-01-20T10:31:00Z"
  }
}
```

**前端集成示例**:
```javascript
// React组件中使用
const fetchGraphData = async (taskId) => {
  try {
    const response = await fetch(`/api/graph-data/${taskId}`);
    const data = await response.json();
    
    // 直接传给Reagraph组件
    setGraphData({
      nodes: data.nodes,
      edges: data.edges
    });
  } catch (error) {
    console.error('获取图谱数据失败:', error);
  }
};
```

## 🏥 健康检查和辅助端点

### GET `/api/health`
```json
{
  "status": "healthy",
  "timestamp": "2024-01-20T10:30:00Z",
  "active_tasks": 3,
  "total_tasks": 15
}
```

### GET `/api/tasks`
```json
{
  "tasks": ["task-id-1", "task-id-2", "task-id-3"],
  "total": 3
}
```

### GET `/`
```json
{
  "message": "AutoGen 知识图谱API服务",
  "version": "1.0.0", 
  "status": "running",
  "docs": "/docs",
  "redoc": "/redoc"
}
```

## 🚀 快速开始

### 1. 启动服务

```bash
# 方式1: 使用启动脚本（推荐）
python start_api.py

# 方式2: 直接使用uvicorn
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# 方式3: 运行主文件
python api/main.py
```

### 2. 验证服务

```bash
# 健康检查
curl http://localhost:8000/api/health

# 查看API文档
# 打开浏览器访问: http://localhost:8000/docs
```

### 3. 完整流程测试

```bash
# 运行自动化测试
python test_api.py

# 分步测试
python test_api.py health    # 健康检查
python test_api.py analysis  # 分析流程
python test_api.py errors    # 错误处理
```

## 🔧 配置说明

### 环境变量
```bash
# API服务配置
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true

# 任务处理配置
MAX_WORKERS=4
TASK_TIMEOUT=300
MAX_TEXT_LENGTH=50000

# 日志配置
LOG_LEVEL=info
LOG_FORMAT=json
```

### 依赖要求
```bash
# 核心依赖
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
pydantic>=2.0.0

# 测试依赖  
requests>=2.31.0
pytest>=7.0.0

# AutoGen依赖
pyautogen>=0.2.35
openai>=1.54.3
neo4j>=5.15.0
```

## 🔍 错误处理

### 常见错误码

| 状态码 | 错误类型 | 说明 |
|--------|----------|------|
| 400 | Bad Request | 请求参数无效 |
| 404 | Not Found | 任务ID不存在 |
| 422 | Validation Error | 数据验证失败 |
| 500 | Internal Error | 服务器内部错误 |

### 错误响应格式
```json
{
  "detail": "任务ID 不存在",
  "error_code": "TASK_NOT_FOUND",
  "timestamp": "2024-01-20T10:30:00Z"
}
```

### 错误处理最佳实践
```python
import requests

def safe_api_call(url, **kwargs):
    """安全的API调用"""
    try:
        response = requests.get(url, timeout=30, **kwargs)
        response.raise_for_status()  # 抛出HTTP错误
        return response.json()
    except requests.exceptions.ConnectionError:
        print("API服务不可用")
        return None
    except requests.exceptions.Timeout:
        print("请求超时")
        return None
    except requests.exceptions.HTTPError as e:
        print(f"HTTP错误: {e.response.status_code}")
        return None
    except Exception as e:
        print(f"未知错误: {e}")
        return None
```

## 🧪 测试指南

### 单元测试
```bash
# 运行所有测试
python -m pytest tests/

# 测试特定模块
python -m pytest tests/test_api.py -v

# 测试覆盖率
python -m pytest --cov=api tests/
```

### 集成测试
```bash
# 完整API流程测试
python test_api.py

# 性能测试
python test_performance.py

# 并发测试
python test_concurrent.py
```

### 手动测试
```bash
# 使用httpie工具
http POST localhost:8000/api/start-analysis text="测试文本"
http GET localhost:8000/api/analysis-status/task-id
http GET localhost:8000/api/graph-data/task-id

# 使用curl
curl -X POST localhost:8000/api/start-analysis \
     -H "Content-Type: application/json" \
     -d '{"text":"测试文本"}'
```

## 📊 性能优化

### 并发处理
- **异步任务**: 使用FastAPI的BackgroundTasks
- **线程池**: ThreadPoolExecutor处理CPU密集任务
- **任务队列**: 内存任务管理器，可扩展为Redis

### 缓存策略
- **结果缓存**: 相同文本的分析结果缓存
- **中间结果**: 缓存实体和关系抽取结果
- **数据压缩**: 大型图谱数据压缩传输

### 监控指标
- **响应时间**: API端点响应时间监控
- **任务处理**: 任务队列长度和处理时间
- **资源使用**: CPU、内存、磁盘使用率

## 🚀 部署指南

### Docker部署
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 生产环境配置
```bash
# 使用Gunicorn + Uvicorn Worker
gunicorn api.main:app -w 4 -k uvicorn.workers.UvicornWorker

# 使用Nginx反向代理
# nginx.conf
server {
    listen 80;
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 🤝 前后端集成

### React集成示例
```jsx
import React, { useState, useEffect } from 'react';
import { GraphCanvas } from 'reagraph';

const KnowledgeGraphApp = () => {
  const [taskId, setTaskId] = useState(null);
  const [graphData, setGraphData] = useState({ nodes: [], edges: [] });
  const [status, setStatus] = useState('idle');

  const analyzeText = async (text) => {
    // 1. 启动分析
    const response = await fetch('/api/start-analysis', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text })
    });
    const { task_id } = await response.json();
    setTaskId(task_id);
    setStatus('processing');

    // 2. 轮询状态
    const checkStatus = async () => {
      const statusResponse = await fetch(`/api/analysis-status/${task_id}`);
      const statusData = await statusResponse.json();
      
      if (statusData.status === 'COMPLETED') {
        // 3. 获取图谱数据
        const graphResponse = await fetch(`/api/graph-data/${task_id}`);
        const graphData = await graphResponse.json();
        setGraphData(graphData);
        setStatus('completed');
      } else if (statusData.status === 'FAILED') {
        setStatus('failed');
      } else {
        setTimeout(checkStatus, 2000);
      }
    };
    
    checkStatus();
  };

  return (
    <div style={{ display: 'flex', height: '100vh' }}>
      <div style={{ width: '30%', padding: '20px' }}>
        <textarea 
          placeholder="输入要分析的文本..."
          onChange={(e) => analyzeText(e.target.value)}
        />
        <div>状态: {status}</div>
      </div>
      <div style={{ width: '70%' }}>
        <GraphCanvas 
          nodes={graphData.nodes}
          edges={graphData.edges}
          layoutType="forceDirected3d"
        />
      </div>
    </div>
  );
};
```

## 📚 开发资源

### API文档
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

### 相关链接
- [FastAPI官方文档](https://fastapi.tiangolo.com/)
- [Pydantic数据验证](https://pydantic-docs.helpmanual.io/)
- [Uvicorn ASGI服务器](https://www.uvicorn.org/)
- [Reagraph图谱组件](https://github.com/reaviz/reagraph)

## 📞 技术支持

如有问题，请检查：
1. API服务是否正常启动 (`python start_api.py`)
2. 端口8000是否被占用
3. 依赖包是否正确安装
4. 网络连接是否正常

---

**🎉 现在您已经拥有了一个完整的、支持异步任务处理的知识图谱API后端！** 