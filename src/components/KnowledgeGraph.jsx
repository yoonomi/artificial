import React, { useState } from 'react';
import { GraphCanvas, darkTheme } from 'reagraph';

const KnowledgeGraph = () => {
  // 状态管理
  const [layout, setLayout] = useState('forceDirected3d');
  const [selections, setSelections] = useState([]);

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

  // 节点交互逻辑
  const handleNodeClick = (node) => {
    console.log('节点被点击:', node);
    setSelections([node.id]);
  };

  const handleNodeContextMenu = (node) => {
    console.log('节点被右键点击:', node);
    alert(`右键点击了: ${node.label} (ID: ${node.id})`);
  };

  // 布局切换处理
  const handleLayoutChange = (event) => {
    const newLayout = event.target.value;
    setLayout(newLayout);
    console.log('布局切换到:', newLayout);
  };

  // 获取布局选项的显示名称
  const getLayoutDisplayName = (layoutValue) => {
    const layoutMap = {
      'forceDirected3d': '3D 力导向图',
      'treeTd3d': '3D 树状图',
      'radialOut3d': '3D 放射状图'
    };
    return layoutMap[layoutValue] || layoutValue;
  };

  return (
    <div style={{ width: '100vw', height: '100vh', background: '#0a0a0a', position: 'relative' }}>
      {/* 布局切换控件 */}
      <div style={{
        position: 'absolute',
        top: '20px',
        left: '20px',
        zIndex: 1000,
        background: 'rgba(15, 15, 30, 0.95)',
        padding: '15px',
        borderRadius: '10px',
        border: '1px solid rgba(0, 212, 255, 0.4)',
        backdropFilter: 'blur(10px)',
        boxShadow: '0 4px 20px rgba(0, 0, 0, 0.8)'
      }}>
        <label style={{
          color: '#00D4FF',
          fontSize: '14px',
          fontWeight: 'bold',
          marginRight: '10px',
          fontFamily: 'Microsoft YaHei, Arial, sans-serif'
        }}>
          🎛️ 切换布局:
        </label>
        <select
          value={layout}
          onChange={handleLayoutChange}
          style={{
            background: 'rgba(0, 0, 0, 0.8)',
            color: '#FFFFFF',
            border: '1px solid rgba(0, 212, 255, 0.6)',
            borderRadius: '6px',
            padding: '8px 12px',
            fontSize: '13px',
            fontFamily: 'Microsoft YaHei, Arial, sans-serif',
            cursor: 'pointer',
            outline: 'none'
          }}
        >
          <option value="forceDirected3d">3D 力导向图</option>
          <option value="treeTd3d">3D 树状图</option>
          <option value="radialOut3d">3D 放射状图</option>
        </select>
      </div>

      {/* 图谱画布 */}
      <GraphCanvas
        nodes={nodes}
        edges={edges}
        layoutType={layout}
        cameraMode="orbit"
        animated={true}
        draggable={true}
        theme={darkTheme}
        sizingType="centrality"
        selections={selections}
        labelType="all"
        onNodeClick={handleNodeClick}
        onNodeContextMenu={handleNodeContextMenu}
        onCanvasClick={() => {
          console.log('点击画布');
          setSelections([]); // 点击空白处取消选择
        }}
      />
      
      {/* 信息面板 */}
      <div style={{
        position: 'absolute',
        top: '20px',
        right: '20px',
        background: 'rgba(15, 15, 30, 0.95)',
        color: 'white',
        padding: '20px',
        borderRadius: '12px',
        fontSize: '14px',
        backdropFilter: 'blur(10px)',
        border: '1px solid rgba(0, 212, 255, 0.3)',
        boxShadow: '0 8px 32px rgba(0, 0, 0, 0.8)',
        fontFamily: 'Microsoft YaHei, Arial, sans-serif',
        maxWidth: '300px'
      }}>
        <h3 style={{ margin: '0 0 15px 0', color: '#00D4FF', fontSize: '18px', textAlign: 'center' }}>
          🧠 AutoGen 3D知识图谱
        </h3>
        <div style={{ fontSize: '12px', opacity: 0.9 }}>
          <div style={{ marginBottom: '8px' }}>🖱️ 左键点击：选择节点高亮</div>
          <div style={{ marginBottom: '8px' }}>🖱️ 右键点击：显示节点信息</div>
          <div style={{ marginBottom: '8px' }}>🔍 滚轮：缩放视图</div>
          <div style={{ marginBottom: '8px' }}>🖱️ 拖拽：旋转/平移</div>
          
          <div style={{ 
            marginTop: '15px', 
            paddingTop: '15px', 
            borderTop: '1px solid rgba(0, 212, 255, 0.3)' 
          }}>
            <div style={{ marginBottom: '5px' }}>📊 节点数: <strong>{nodes.length}</strong></div>
            <div style={{ marginBottom: '5px' }}>🔗 关系数: <strong>{edges.length}</strong></div>
            <div style={{ marginBottom: '5px' }}>🎨 主题: <strong>深色科技风</strong></div>
            <div style={{ marginBottom: '5px' }}>📏 节点大小: <strong>基于中心度</strong></div>
            <div style={{ marginBottom: '5px' }}>🎛️ 当前布局: <strong>{getLayoutDisplayName(layout)}</strong></div>
            <div style={{ marginBottom: '5px' }}>
              ✨ 选中节点: <strong>{selections.length > 0 ? selections.join(', ') : '无'}</strong>
            </div>
          </div>

          <div style={{
            marginTop: '15px',
            padding: '10px',
            background: 'rgba(0, 212, 255, 0.1)',
            border: '1px solid rgba(0, 212, 255, 0.3)',
            borderRadius: '8px',
            fontSize: '11px'
          }}>
            <div style={{ fontWeight: 'bold', marginBottom: '5px', color: '#00D4FF' }}>
              🚀 交互功能:
            </div>
            <div>• 动态布局切换</div>
            <div>• 智能节点高亮</div>
            <div>• 右键菜单信息</div>
            <div>• 实时状态显示</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default KnowledgeGraph; 