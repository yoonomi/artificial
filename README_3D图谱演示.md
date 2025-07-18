# AutoGen 3D知识图谱演示

## 🎯 项目概述

本演示展示了如何将AutoGen知识图谱生成系统提取的中文数据，通过React+Reagraph或纯HTML+Three.js渲染成3D可交互图谱。

## 📁 文件说明

### 1. React版本 (推荐)
- `src/components/KnowledgeGraph.jsx` - 主要的3D图谱组件
- `src/App.js` - React应用入口
- `package.json` - 项目依赖配置

### 2. HTML演示版本 (即用版)
- `demo.html` - 独立的HTML文件，可直接在浏览器中打开

## 🚀 快速体验

### 方法一：直接运行HTML演示
```bash
# 直接用浏览器打开
open demo.html
# 或者用双击打开
```

### 方法二：运行React版本
```bash
# 安装依赖
npm install

# 启动开发服务器
npm start

# 浏览器访问 http://localhost:3000
```

## 🎨 功能特性

### 3D交互功能
- **🖱️ 鼠标左键拖动**：旋转3D视角
- **🔍 鼠标滚轮**：缩放视图
- **🖱️ 鼠标右键拖动**：平移整个图谱
- **👆 点击节点**：查看节点详细信息

### 可视化特性
- **3D力导向布局**：节点在3D空间中自然分布
- **动态标签**：所有节点显示中文标签
- **颜色编码**：不同类型的节点使用不同颜色
- **发光效果**：节点具有光晕效果
- **实时统计**：显示节点和边的数量

### 数据特性
- **中文支持**：完整支持中文节点标签
- **真实数据**：基于AutoGen系统提取的AI领域知识
- **关系映射**：显示实体间的语义关系

## 🔧 技术栈

### React版本
- **React 18** - 前端框架
- **Reagraph 4.15+** - 3D图谱可视化库
- **Three.js** - 底层3D引擎

### HTML版本
- **Three.js r128** - 3D图形库
- **OrbitControls** - 3D视角控制
- **原生JavaScript** - 交互逻辑

## 📊 数据结构

### 节点数据格式
```javascript
{
  id: 'n-1',
  label: '人工智能技术',
  fill: '#FF6B6B',
  size: 15
}
```

### 边数据格式
```javascript
{
  id: 'e-1',
  source: 'n-2',
  target: 'n-3',
  label: '开发',
  size: 3
}
```

## 🎯 知识图谱内容

当前演示包含AI领域的15个核心概念：

### 人物节点
- 阿兰·图灵
- 李世石

### 技术节点
- 人工智能技术
- 深度学习
- 机器学习
- 自然语言处理
- 计算机视觉
- 神经网络

### 产品节点
- GPT
- ChatGPT
- AlphaGo
- 图灵测试

### 机构节点
- OpenAI
- DeepMind
- 腾讯

### 关系类型
- 开发、包含、基于、提出、奠定基础、击败、应用领域、研发

## ⚙️ 自定义配置

### 修改节点数据
编辑组件中的`nodes`数组：
```javascript
const nodes = [
  {
    id: 'your-id',
    label: '你的标签',
    fill: '#your-color',
    size: 12
  }
  // ... 更多节点
];
```

### 修改关系数据
编辑组件中的`edges`数组：
```javascript
const edges = [
  {
    id: 'your-edge-id',
    source: 'source-node-id',
    target: 'target-node-id',
    label: '关系标签'
  }
  // ... 更多关系
];
```

### 主题配置
修改`theme`对象来自定义外观：
```javascript
theme={{
  canvas: {
    background: '#0a0a0a'  // 背景色
  },
  node: {
    activeFill: '#FF6B6B',  // 活跃节点颜色
    opacity: 0.9            // 透明度
  },
  label: {
    color: '#FFFFFF',       // 标签颜色
    fontSize: 10            // 字体大小
  }
}}
```

## 🔄 集成AutoGen数据

### 1. 从AutoGen获取数据
```python
# 在AutoGen系统中
entities = ece_agent.process(text)  # 提取实体
relationships = ree_agent.process(text, entities)  # 提取关系
```

### 2. 数据格式转换
```javascript
// 将AutoGen格式转换为图谱格式
function convertAutoGenData(entities, relationships) {
  const nodes = entities.map((entity, index) => ({
    id: entity.unique_id || `n-${index}`,
    label: entity.text || entity.name,
    fill: getColorByType(entity.label),
    size: getSizeByImportance(entity)
  }));

  const edges = relationships.map((rel, index) => ({
    id: `e-${index}`,
    source: rel.source_entity_id,
    target: rel.target_entity_id,
    label: rel.relationship_type
  }));

  return { nodes, edges };
}
```

## 🐛 常见问题

### Q: 图谱不显示怎么办？
A: 检查浏览器控制台错误，确保Three.js库正确加载。

### Q: 中文标签显示异常？
A: 确保字体设置包含中文字体："Microsoft YaHei", Arial。

### Q: 性能卡顿怎么办？
A: 减少节点数量或降低渲染质量（减少几何体面数）。

### Q: npm安装失败？
A: 使用HTML版本或尝试yarn替代npm。

## 🎉 成功标准

当您在浏览器中看到：
1. ✅ 3D空间中的彩色节点球体
2. ✅ 连接节点的蓝色线条
3. ✅ 中文标签正确显示
4. ✅ 鼠标交互流畅响应
5. ✅ 控制面板显示统计信息

说明3D知识图谱已成功搭建！

## 📞 技术支持

如遇问题，请：
1. 检查浏览器控制台错误信息
2. 确认网络连接（CDN加载）
3. 尝试不同浏览器（推荐Chrome）
4. 参考项目README文档

---

🎊 **恭喜！您的AutoGen 3D知识图谱演示已准备就绪！** 