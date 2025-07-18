"""
项目配置文件
"""

import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    """项目配置类"""
    
    # 基础配置
    PROJECT_NAME = os.getenv("PROJECT_NAME", "autogen_kg_project")
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # Neo4j数据库配置
    NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
    
    # OpenAI API配置
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4")
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")  # 支持自定义API基础URL，如Silicon Flow
    
    # API配置
    API_HOST = os.getenv("API_HOST", "localhost")
    API_PORT = int(os.getenv("API_PORT", "8000"))
    
    # 文件路径配置
    DATA_DIR = "data"
    LOGS_DIR = "logs"
    OUTPUT_DIR = "output"
    
    # AutoGen配置
    AUTOGEN_CONFIG = {
        "llm_config": {
            "model": OPENAI_MODEL,
            "api_key": OPENAI_API_KEY,
            "temperature": 0.1,
            "max_tokens": 2000,
        },
        "code_execution_config": {
            "work_dir": "temp",
            "use_docker": False,
        }
    }
    
    # 专门的GPT-4高推理配置（用于首席本体论家等专家智能体）
    @property
    def llm_config_gpt4(self):
        """高推理能力的LLM配置"""
        config = {
            "model": "deepseek-ai/DeepSeek-V3",  # 使用DeepSeek-V3模型
            "api_key": self.OPENAI_API_KEY,
            "temperature": 0.1,
            "max_tokens": 2000,
            "timeout": 120,  # 增加超时时间到120秒
        }
        
        # 如果设置了自定义base_url，则添加到配置中
        if self.OPENAI_BASE_URL:
            config["base_url"] = self.OPENAI_BASE_URL
            
        return config

    # 知识图谱配置
    GRAPH_CONFIG = {
        "node_limit": 1000,
        "relationship_limit": 5000,
        "max_depth": 5,
        "enable_temporal": True,
        "enable_inference": True,
    }

# 创建配置实例
config = Config() 