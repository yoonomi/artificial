# 推理智能体工具集使用指南

## 概述

推理智能体工具集为知识图谱提供了自动化的推理分析功能，能够发现数据中的隐含关系并创建推理连接。该工具集包含三个核心功能模块：

1. **模式发现** (`find_interesting_patterns`)
2. **假设验证** (`verify_hypothesis_from_text`) 
3. **推理关系创建** (`create_inferred_relationship`)

## 核心功能

### 1. 模式发现 (find_interesting_patterns)

**功能**：在Neo4j图谱中主动寻找预设的、可能暗示隐含关系的模式。

**支持的模式类型**：
- `common_workplace`: 寻找在同一机构工作的人员 → 推理**同事关系**
- `common_education`: 寻找在同一教育机构学习的人员 → 推理**校友关系**
- `collaboration_through_project`: 寻找参与同一项目的人员 → 推理**合作关系**
- `mentor_student_pattern`: 寻找可能的师生关系模式 → 推理**师生关系**
- `technology_transfer`: 寻找技术传承或影响关系 → 推理**技术影响**

**返回格式**：
```python
[
    {
        'type': 'common_workplace',
        'description': '寻找在同一机构工作的人员',
        'inferred_relationship': '同事关系',
        'entities': {'person1': '张三', 'person2': '李四', 'organization': '中国移动'},
        'confidence': 'unknown'
    },
    ...
]
```

### 2. 假设验证 (verify_hypothesis_from_text)

**功能**：验证发现的模式是否真的能构成有意义的隐含关系。

**验证过程**：
1. 根据模式中的实体，从Neo4j中提取相关的`source_sentence`属性
2. 将这些句子合并为证据文本
3. 使用LLM (DeepSeek-V3) 分析证据文本，评估关系的可能性
4. 返回置信度等级：**高**、**中**、**低**

**返回格式**：
```python
{
    'type': 'common_workplace',
    'verification': '高',
    'evidence_text': '张三在中国移动担任高级工程师...',
    'reasoning': '证据文本明确表明两人在同一机构工作...',
    ...
}
```

### 3. 推理关系创建 (create_inferred_relationship)

**功能**：将验证为高可能性的隐含关系写回Neo4j图谱。

**创建的关系特征**：
- 关系类型：`推理_同事`、`推理_合作`、`推理_师生`等
- 关系属性：
  - `type`: 'INFERRED'
  - `confidence`: 置信度级别
  - `reasoning`: LLM推理过程
  - `evidence_summary`: 证据摘要
  - `pattern_type`: 发现的模式类型

## 完整推理管道

### execute_reasoning_pipeline 函数

提供一键式的完整推理流程：

```python
from tools.graph_db import GraphDB
from tools.reasoning_tools import execute_reasoning_pipeline

# 初始化数据库连接
db = GraphDB(uri="bolt://localhost:7687", username="neo4j", password="password")

# 执行推理管道
result = execute_reasoning_pipeline(db, confidence_threshold='中')

print(f"发现模式: {result['patterns_found']} 个")
print(f"成功创建关系: {result['relationships_created']} 个")
```

**置信度阈值选项**：
- `'高'`: 只创建高置信度关系
- `'中'`: 创建中等和高置信度关系  
- `'低'`: 创建所有置信度关系

## 使用示例

### 1. 运行单元测试

```bash
python run_tests.py reasoning
```

### 2. 运行完整演示

```bash
python test_reasoning_demo.py
```

### 3. 自定义使用

```python
from tools.graph_db import GraphDB
from tools.reasoning_tools import (
    find_interesting_patterns,
    verify_hypothesis_from_text,
    create_inferred_relationship
)

# 连接数据库
db = GraphDB(uri="bolt://localhost:7687", username="neo4j", password="password")

# 步骤1: 发现模式
patterns = find_interesting_patterns(db)
print(f"发现 {len(patterns)} 个潜在模式")

# 步骤2: 验证第一个模式
if patterns:
    verified_pattern = verify_hypothesis_from_text(patterns[0], db)
    print(f"验证结果: {verified_pattern['verification']}")
    
    # 步骤3: 创建关系（如果置信度足够高）
    if verified_pattern['verification'] == '高':
        result = create_inferred_relationship(verified_pattern, db)
        print(f"关系创建结果: {result}")
```

## 系统要求

### 环境依赖
- Python 3.8+
- Neo4j 数据库
- Silicon Flow API (DeepSeek-V3 模型)

### 必需的Python包
```
neo4j
openai
python-dotenv
```

### 环境变量配置

在 `.env` 文件中配置：
```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password

OPENAI_API_KEY=your_silicon_flow_api_key
OPENAI_BASE_URL=https://api.siliconflow.cn/v1
OPENAI_MODEL=deepseek-ai/DeepSeek-V3
```

## 数据要求

为了使推理工具有效工作，图谱中的关系需要包含 `source_sentence` 属性，该属性存储支持该关系的原始文本证据。

**示例关系创建**：
```cypher
CREATE (p1:人物 {name: '张三'})-[:工作于 {
    source_sentence: '张三在中国移动担任高级工程师，负责5G网络优化工作。'
}]->(o:机构 {name: '中国移动'})
```

## 输出结果

### 推理关系示例

运行推理管道后，将在图谱中创建新的推理关系：

```cypher
// 查询推理关系
MATCH (a)-[r]->(b) 
WHERE r.type = 'INFERRED'
RETURN a.name, type(r), b.name, r.confidence

// 示例结果:
// 张三 --[推理_同事]--> 李四 (置信度: 高)
// 王五 --[推理_合作]--> 赵六 (置信度: 高)
```

### 性能指标

- **模式发现速度**: ~50ms per pattern type
- **LLM验证时间**: ~3-7秒 per pattern
- **关系创建速度**: ~10ms per relationship

## 故障排除

### 常见问题

1. **未发现任何模式**
   - 检查图谱中是否有符合模式的数据结构
   - 确认节点标签和关系类型与预定义模式匹配

2. **LLM验证失败**
   - 检查API密钥和网络连接
   - 确认 `source_sentence` 属性存在

3. **关系创建失败**
   - 检查实体名称是否正确
   - 确认数据库连接正常

### 调试模式

启用详细日志：
```python
import logging
logging.basicConfig(level=logging.INFO)
```

## 扩展功能

### 添加新的模式类型

在 `tools/reasoning_tools.py` 的 `PATTERN_QUERIES` 字典中添加新模式：

```python
PATTERN_QUERIES["new_pattern"] = {
    "description": "模式描述",
    "cypher": "MATCH ... RETURN ...",
    "inferred_relationship": "推理关系类型"
}
```

### 自定义验证逻辑

可以修改 `verify_hypothesis_from_text` 函数中的提示词来调整验证标准。

---

通过这个推理工具集，您可以自动化地发现知识图谱中的隐含关系，为知识图谱增加更丰富的语义连接。 