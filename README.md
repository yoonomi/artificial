# AutoGen 知识图谱生成系统

一个基于多智能体架构的自动化知识图谱构建系统，具备完整的溯源信息追踪和高级推理功能。

## 🚀 项目特性

### 核心功能
- **多智能体协作**：采用专业化智能体分工合作的架构
- **溯源信息追踪**：每个知识元素都能追溯到原始文本句子
- **自动图谱构建**：从文本到Neo4j数据库的端到端自动化
- **高级推理功能**：发现隐含知识关系并验证推理结果
- **完整测试覆盖**：包含单元测试、集成测试和端到端测试

### 智能体架构
- **首席本体论专家**：设计知识图谱的实体和关系类型
- **ECE智能体**：实体抽取和分类（Entity Classification & Extraction）
- **REE智能体**：关系抽取和推理（Relationship Extraction & Estimation）
- **图谱合成智能体**：生成Neo4j Cypher查询语句
- **高级推理智能体**：发现隐含知识关系并进行验证

## 📋 系统要求

- Python 3.8+
- Neo4j 4.0+
- OpenAI API Key 或兼容的LLM API

## 🛠️ 安装配置

1. **克隆项目**
```bash
git clone https://github.com/yoonomi/artificial.git
cd artificial
```

2. **创建虚拟环境**
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **配置API**
编辑 `config.py` 文件，设置你的LLM API配置：
```python
# LLM配置示例
LLM_CONFIG = {
    "model": "deepseek-ai/DeepSeek-V3",
    "api_key": "your-api-key-here",
    "base_url": "https://api.siliconflow.cn/v1",
    "temperature": 0.1
}
```

5. **启动Neo4j数据库**
确保Neo4j数据库运行在 `bolt://localhost:7687`

## 🎯 快速开始

### 基础使用
```bash
# 运行主程序
python main.py

# 运行带推理功能的程序
python main_with_reasoning.py

# 运行简化版程序
python main_simple.py
```

### 测试系统
```bash
# 运行所有测试
python run_tests.py all

# 运行特定测试
python run_tests.py source-sentence  # 溯源信息测试
python run_tests.py end-to-end       # 端到端测试
python run_tests.py reasoning        # 推理功能测试
```

## 📊 系统架构

```
文本输入
    ↓
首席本体论专家（本体设计）
    ↓
ECE智能体（实体抽取 + 溯源）
    ↓
REE智能体（关系抽取 + 溯源）
    ↓
图谱合成智能体（Cypher生成）
    ↓
Neo4j数据库存储
    ↓
高级推理智能体（隐含关系发现）
```

## 💡 技术亮点

### 1. 完整溯源追踪
- 每个实体和关系都包含 `source_sentence` 属性
- 从原始文本到数据库的完整可追溯性
- 支持知识来源验证和审计

### 2. 智能Cypher生成
- 使用 `MERGE...ON CREATE SET` 模式存储节点
- 使用 `MATCH...MERGE...SET` 模式处理关系
- 自动字符串转义防止注入攻击

### 3. 高级推理功能
- 模式发现：同事关系、合作关系、师生关系等
- 假设验证：基于文本证据验证推理结果
- 知识扩展：自动发现隐含的知识关系

### 4. robust测试框架
- 单元测试：每个智能体独立测试
- 集成测试：多智能体协作测试
- 端到端测试：完整流程验证
- 自动化测试：支持持续集成

## 📁 项目结构

```
AutoGen/
├── agents/                  # 智能体模块
│   ├── chief_ontologist.py    # 首席本体论专家
│   ├── ece_agent.py           # 实体抽取智能体
│   ├── ree_agent.py           # 关系抽取智能体
│   ├── graph_synthesis_agent.py # 图谱合成智能体
│   └── advanced_reasoning_agent.py # 高级推理智能体
├── tools/                   # 工具模块
│   ├── graph_db.py           # Neo4j数据库操作
│   ├── reasoning_tools.py    # 推理工具函数
│   └── text_processing.py   # 文本处理工具
├── api/                     # API接口
├── data/                    # 测试数据
├── test_*.py               # 测试文件
├── main*.py               # 主程序文件
├── config.py              # 配置文件
└── requirements.txt       # 依赖列表
```

## 🔧 配置说明

### Neo4j配置
```python
NEO4J_CONFIG = {
    "uri": "bolt://localhost:7687",
    "user": "neo4j",
    "password": "your-password"
}
```

### LLM配置
支持多种LLM提供商：
- OpenAI GPT系列
- DeepSeek系列
- 其他兼容OpenAI API的服务

## 📈 使用示例

### 基础知识图谱构建
```python
from agents.ece_agent import create_ece_agent
from agents.ree_agent import create_ree_agent
from agents.graph_synthesis_agent import create_graph_synthesis_agent

# 创建智能体
ece_agent = create_ece_agent()
ree_agent = create_ree_agent()
graph_agent = create_graph_synthesis_agent()

# 处理文本
text = "你的文本内容..."
entities = ece_agent.process(text)
relationships = ree_agent.process(text, entities)
cypher_queries = graph_agent.process(entities, relationships)
```

### 高级推理功能
```python
from agents.advanced_reasoning_agent import create_advanced_reasoning_agent

reasoning_agent = create_advanced_reasoning_agent()
# 自动发现隐含关系
patterns = reasoning_agent.find_patterns()
# 验证推理结果
verified_patterns = reasoning_agent.verify_patterns(patterns)
```

## 🧪 测试结果

项目包含完整的测试套件，验证以下功能：
- ✅ ECE智能体实体抽取和溯源
- ✅ REE智能体关系抽取和溯源
- ✅ 图谱合成和Cypher生成
- ✅ Neo4j数据库存储和查询
- ✅ 高级推理和模式发现
- ✅ 端到端系统集成

## 📚 文档

详细文档请参考：
- [溯源信息功能文档](README_溯源信息改造完成.md)
- [图谱合成升级文档](README_图谱合成智能体升级完成.md)
- [高级推理功能文档](README_高级推理智能体集成.md)
- [推理工具使用指南](README_推理工具使用指南.md)

## 🤝 贡献

欢迎提交Issue和Pull Request来帮助改进项目！

## 📄 许可证

MIT License

## 📞 联系

如有问题，请通过GitHub Issues联系。 