"""
AutoGen知识图谱生成系统 - API包

该包包含了Web API相关的模块:
- main: FastAPI应用主文件
- models: 数据模型定义
"""

from .main import app
from .models import *

__all__ = ['app'] 