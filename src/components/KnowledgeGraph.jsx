import React from 'react';
import { GraphCanvas, darkTheme } from 'reagraph';

const KnowledgeGraph = () => {
  // 模拟从AutoGen系统提取的中文知识图谱数据
  const nodes = [
    {
      id: 'n-1',
      label: '人工智能技术',
      fill: '#FF6B6B',
      size: 15
    },
    {
      id: 'n-2',
      label: 'OpenAI',
      fill: '#4ECDC4',
      size: 12
    },
    {
      id: 'n-3',
      label: 'GPT',
      fill: '#45B7D1',
      size: 10
    },
    {
      id: 'n-4',
      label: 'ChatGPT',
      fill: '#96CEB4',
      size: 10
    },
    {
      id: 'n-5',
      label: 'DeepMind',
      fill: '#FFEAA7',
      size: 12
    },
    {
      id: 'n-6',
      label: 'AlphaGo',
      fill: '#DDA0DD',
      size: 10
    },
    {
      id: 'n-7',
      label: '深度学习',
      fill: '#98D8C8',
      size: 13
    },
    {
      id: 'n-8',
      label: '机器学习',
      fill: '#A8E6CF',
      size: 13
    },
    {
      id: 'n-9',
      label: '自然语言处理',
      fill: '#FFB6C1',
      size: 11
    },
    {
      id: 'n-10',
      label: '计算机视觉',
      fill: '#87CEEB',
      size: 11
    },
    {
      id: 'n-11',
      label: '阿兰·图灵',
      fill: '#F0E68C',
      size: 9
    },
    {
      id: 'n-12',
      label: '图灵测试',
      fill: '#E6E6FA',
      size: 8
    },
    {
      id: 'n-13',
      label: '神经网络',
      fill: '#FFA07A',
      size: 12
    },
    {
      id: 'n-14',
      label: '李世石',
      fill: '#20B2AA',
      size: 8
    },
    {
      id: 'n-15',
      label: '腾讯',
      fill: '#DAA520',
      size: 10
    }
  ];

  const edges = [
    {
      id: 'e-1',
      source: 'n-2',
      target: 'n-3',
      label: '开发',
      size: 3
    },
    {
      id: 'e-2',
      source: 'n-2',
      target: 'n-4',
      label: '开发',
      size: 3
    },
    {
      id: 'e-3',
      source: 'n-3',
      target: 'n-4',
      label: '基础模型',
      size: 2
    },
    {
      id: 'e-4',
      source: 'n-5',
      target: 'n-6',
      label: '开发',
      size: 3
    },
    {
      id: 'e-5',
      source: 'n-1',
      target: 'n-7',
      label: '包含',
      size: 4
    },
    {
      id: 'e-6',
      source: 'n-1',
      target: 'n-8',
      label: '包含',
      size: 4
    },
    {
      id: 'e-7',
      source: 'n-1',
      target: 'n-9',
      label: '包含',
      size: 3
    },
    {
      id: 'e-8',
      source: 'n-1',
      target: 'n-10',
      label: '包含',
      size: 3
    },
    {
      id: 'e-9',
      source: 'n-7',
      target: 'n-13',
      label: '基于',
      size: 3
    },
    {
      id: 'e-10',
      source: 'n-8',
      target: 'n-7',
      label: '包含',
      size: 3
    },
    {
      id: 'e-11',
      source: 'n-11',
      target: 'n-12',
      label: '提出',
      size: 2
    },
    {
      id: 'e-12',
      source: 'n-11',
      target: 'n-1',
      label: '奠定基础',
      size: 4
    },
    {
      id: 'e-13',
      source: 'n-6',
      target: 'n-14',
      label: '击败',
      size: 2
    },
    {
      id: 'e-14',
      source: 'n-9',
      target: 'n-3',
      label: '应用领域',
      size: 3
    },
    {
      id: 'e-15',
      source: 'n-15',
      target: 'n-1',
      label: '研发',
      size: 3
    }
  ];

  return (
    <div style={{ width: '100vw', height: '100vh', background: '#0a0a0a' }}>
      <GraphCanvas
        nodes={nodes}
        edges={edges}
        layoutType="forceDirected3d"
        cameraMode="orbit"
        animated={true}
        draggable={true}
        theme={darkTheme}
        sizingType="centrality"
        labelType="all"
        onNodeClick={(node) => {
          console.log('点击节点:', node);
        }}
        onEdgeClick={(edge) => {
          console.log('点击边:', edge);
        }}
        onCanvasClick={() => {
          console.log('点击画布');
        }}
      />
      
      {/* 控制面板 */}
      <div style={{
        position: 'absolute',
        top: '20px',
        left: '20px',
        background: 'rgba(0, 0, 0, 0.8)',
        color: 'white',
        padding: '15px',
        borderRadius: '8px',
        fontFamily: 'Microsoft YaHei, Arial, sans-serif',
        fontSize: '14px',
        backdropFilter: 'blur(10px)'
      }}>
        <h3 style={{ margin: '0 0 10px 0', color: '#00D4FF' }}>AutoGen 3D知识图谱</h3>
        <div style={{ fontSize: '12px', opacity: 0.8 }}>
          <div>🖱️ 左键拖动：旋转视角</div>
          <div>🔍 滚轮：缩放</div>
          <div>🖱️ 右键拖动：平移</div>
          <div>📊 节点数: {nodes.length}</div>
          <div>🔗 关系数: {edges.length}</div>
          <div>🎨 主题: 深色科技风</div>
          <div>📏 节点大小: 基于中心度</div>
        </div>
      </div>
    </div>
  );
};

export default KnowledgeGraph; 