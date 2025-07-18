import React, { useState, useMemo } from 'react';
import { GraphCanvas, darkTheme } from 'reagraph';

const KnowledgeGraph = ({ graphData }) => {
  // 状态管理
  const [layout, setLayout] = useState('forceDirected3d');
  const [selections, setSelections] = useState([]);
  const [showClusters, setShowClusters] = useState(true); // 控制是否显示集群模式

  // 如果没有传入数据，使用默认数据
  const defaultData = {
    nodes: [
      {
        id: 'n-1',
        label: '人工智能',
        clusterId: 'cluster_ai',
        clusterName: 'AI技术',
        color: '#FF6B6B',
        size: 2.5,
        type: 'concept'
      },
      {
        id: 'n-2',
        label: '机器学习',
        clusterId: 'cluster_ai',
        clusterName: 'AI技术',
        color: '#FF6B6B',
        size: 2.0,
        type: 'concept'
      },
      {
        id: 'n-3',
        label: '深度学习',
        clusterId: 'cluster_ai',
        clusterName: 'AI技术',
        color: '#FF6B6B',
        size: 1.8,
        type: 'concept'
      },
      {
        id: 'n-4',
        label: '计算机',
        clusterId: 'cluster_tech',
        clusterName: '技术系统',
        color: '#4ECDC4',
        size: 2.0,
        type: 'concept'
      },
      {
        id: 'n-5',
        label: '系统',
        clusterId: 'cluster_tech',
        clusterName: '技术系统',
        color: '#4ECDC4',
        size: 1.5,
        type: 'concept'
      },
      {
        id: 'n-6',
        label: '数据',
        clusterId: 'cluster_tech',
        clusterName: '技术系统',
        color: '#4ECDC4',
        size: 1.8,
        type: 'concept'
      }
    ],
    edges: [
      {
        id: 'e-1',
        source: 'n-1',
        target: 'n-2',
        label: '包含',
        size: 2
      },
      {
        id: 'e-2',
        source: 'n-2',
        target: 'n-3',
        label: '包含',
        size: 1.5
      },
      {
        id: 'e-3',
        source: 'n-4',
        target: 'n-5',
        label: '相关',
        size: 1.5
      }
    ],
    clusters: {
      cluster_ai: { name: 'AI技术', count: 3, color: '#FF6B6B' },
      cluster_tech: { name: '技术系统', count: 3, color: '#4ECDC4' }
    }
  };

  const currentData = graphData || defaultData;

  // 生成集群节点和边
  const clusterData = useMemo(() => {
    if (!showClusters || !currentData.clusters) {
      return {
        nodes: currentData.nodes || [],
        edges: currentData.edges || []
      };
    }

    // 创建集群节点
    const clusterNodes = [];
    const clusterEdges = [];
    
    // 统计每个集群的信息
    Object.entries(currentData.clusters).forEach(([clusterId, clusterInfo]) => {
      // 计算集群节点大小（基于成员数量）
      const clusterSize = Math.max(3, Math.min(8, clusterInfo.count * 1.5));
      
      const clusterNode = {
        id: `cluster-${clusterId}`,
        label: `${clusterInfo.name} (${clusterInfo.count})`,
        size: clusterSize,
        color: clusterInfo.color,
        type: 'cluster',
        clusterId: clusterId,
        memberCount: clusterInfo.count,
        // 添加集群特有属性
        fill: clusterInfo.color,
        stroke: '#ffffff',
        strokeWidth: 2
      };
      
      clusterNodes.push(clusterNode);
    });

    // 创建集群间的连接（基于原始节点间的关系）
    const clusterConnections = new Map();
    
    currentData.edges?.forEach(edge => {
      const sourceNode = currentData.nodes.find(n => n.id === edge.source);
      const targetNode = currentData.nodes.find(n => n.id === edge.target);
      
      if (sourceNode && targetNode && sourceNode.clusterId !== targetNode.clusterId) {
        const connectionKey = `${sourceNode.clusterId}-${targetNode.clusterId}`;
        const reverseKey = `${targetNode.clusterId}-${sourceNode.clusterId}`;
        
        if (!clusterConnections.has(connectionKey) && !clusterConnections.has(reverseKey)) {
          clusterConnections.set(connectionKey, {
            sourceCluster: sourceNode.clusterId,
            targetCluster: targetNode.clusterId,
            weight: 1
          });
        } else {
          // 增加连接权重
          const existing = clusterConnections.get(connectionKey) || clusterConnections.get(reverseKey);
          if (existing) existing.weight += 1;
        }
      }
    });

    // 生成集群间的边
    clusterConnections.forEach((connection, key) => {
      clusterEdges.push({
        id: `cluster-edge-${key}`,
        source: `cluster-${connection.sourceCluster}`,
        target: `cluster-${connection.targetCluster}`,
        label: `关联 (${connection.weight})`,
        size: Math.max(1, Math.min(4, connection.weight)),
        color: '#00D4FF',
        type: 'cluster-connection'
      });
    });

    return {
      nodes: clusterNodes,
      edges: clusterEdges
    };
  }, [currentData, showClusters]);

  // 事件处理函数
  const handleLayoutChange = (event) => {
    setLayout(event.target.value);
    console.log('布局已切换到:', event.target.value);
  };

  const handleNodeClick = (node) => {
    console.log('点击节点:', node);
    if (selections.includes(node.id)) {
      setSelections(selections.filter(id => id !== node.id));
    } else {
      setSelections([...selections, node.id]);
    }
  };

  const handleNodeContextMenu = (node) => {
    console.log('右键点击节点:', node);
    
    let message = `节点信息:\n`;
    message += `标签: ${node.label}\n`;
    message += `ID: ${node.id}\n`;
    message += `类型: ${node.type === 'cluster' ? '集群节点' : '概念节点'}\n`;
    
    if (node.type === 'cluster') {
      message += `成员数量: ${node.memberCount}\n`;
      message += `集群ID: ${node.clusterId}`;
    } else if (node.clusterId) {
      message += `所属集群: ${node.clusterName || node.clusterId}`;
    }
    
    alert(message);
  };

  const toggleClusterMode = () => {
    setShowClusters(!showClusters);
    setSelections([]); // 切换模式时清空选择
  };

  const getLayoutDisplayName = (layoutValue) => {
    const layoutMap = {
      'forceDirected3d': '3D 力导向图',
      'treeTd3d': '3D 树状图',
      'radialOut3d': '3D 放射状图'
    };
    return layoutMap[layoutValue] || layoutValue;
  };

  return (
    <div style={{ width: '100%', height: '100%', background: '#0a0a0a', position: 'relative' }}>
      {/* 控制面板 */}
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
        {/* 集群模式切换 */}
        <div style={{ marginBottom: '15px' }}>
          <label style={{
            color: '#00D4FF',
            fontSize: '14px',
            fontWeight: 'bold',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontFamily: 'Microsoft YaHei, Arial, sans-serif'
          }}>
            <input
              type="checkbox"
              checked={showClusters}
              onChange={toggleClusterMode}
              style={{ 
                transform: 'scale(1.2)',
                cursor: 'pointer'
              }}
            />
            🧩 集群模式
          </label>
        </div>
        
        {/* 布局切换 */}
        <div>
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
      </div>

      {/* 图谱画布 */}
      <GraphCanvas
        nodes={clusterData.nodes}
        edges={clusterData.edges}
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
        // 集群相关配置
        clusterAttribute="clusterId"
        clusteringEnabled={showClusters}
        minNodeSize={1}
        maxNodeSize={8}
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
        maxWidth: '320px'
      }}>
        <h3 style={{ margin: '0 0 15px 0', color: '#00D4FF', fontSize: '18px', textAlign: 'center' }}>
          🧠 AutoGen 知识图谱
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
            <div style={{ marginBottom: '5px' }}>
              📊 {showClusters ? '集群' : '节点'}数: <strong>{clusterData.nodes.length}</strong>
            </div>
            <div style={{ marginBottom: '5px' }}>
              🔗 关系数: <strong>{clusterData.edges.length}</strong>
            </div>
            {currentData.clusters && (
              <div style={{ marginBottom: '5px' }}>
                🧩 原始集群: <strong>{Object.keys(currentData.clusters).length}</strong>
              </div>
            )}
            <div style={{ marginBottom: '5px' }}>
              🎨 显示模式: <strong>{showClusters ? '集群模式' : '详细模式'}</strong>
            </div>
            <div style={{ marginBottom: '5px' }}>
              🎛️ 当前布局: <strong>{getLayoutDisplayName(layout)}</strong>
            </div>
            <div style={{ marginBottom: '5px' }}>
              ✨ 选中节点: <strong>{selections.length > 0 ? selections.length : '无'}</strong>
            </div>
          </div>

          {/* 集群信息显示 */}
          {showClusters && currentData.clusters && (
            <div style={{
              marginTop: '15px',
              padding: '10px',
              background: 'rgba(0, 212, 255, 0.1)',
              border: '1px solid rgba(0, 212, 255, 0.3)',
              borderRadius: '8px',
              fontSize: '11px'
            }}>
              <div style={{ fontWeight: 'bold', marginBottom: '8px', color: '#00D4FF' }}>
                🧩 集群统计:
              </div>
              {Object.entries(currentData.clusters).map(([clusterId, info]) => (
                <div key={clusterId} style={{ 
                  marginBottom: '4px', 
                  display: 'flex', 
                  alignItems: 'center',
                  gap: '8px'
                }}>
                  <div style={{
                    width: '12px',
                    height: '12px',
                    borderRadius: '50%',
                    backgroundColor: info.color,
                    flexShrink: 0
                  }}></div>
                  <span>{info.name}: {info.count}</span>
                </div>
              ))}
            </div>
          )}

          <div style={{
            marginTop: '15px',
            padding: '10px',
            background: 'rgba(0, 212, 255, 0.1)',
            border: '1px solid rgba(0, 212, 255, 0.3)',
            borderRadius: '8px',
            fontSize: '11px'
          }}>
            <div style={{ fontWeight: 'bold', marginBottom: '5px', color: '#00D4FF' }}>
              🚀 新功能:
            </div>
            <div>• 集群化智能显示</div>
            <div>• 动态模式切换</div>
            <div>• 层次化信息展示</div>
            <div>• 集群间关系分析</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default KnowledgeGraph; 