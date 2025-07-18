import React, { useState, useEffect } from 'react';
import { GraphCanvas, darkTheme } from 'reagraph';
import './AnalysisPage.css';

const AnalysisPage = () => {
  // 状态管理
  const [inputText, setInputText] = useState('');
  const [taskId, setTaskId] = useState(null);
  const [analysisStatus, setAnalysisStatus] = useState('idle'); // idle, pending, processing, completed, failed
  const [progress, setProgress] = useState(0);
  const [statusMessage, setStatusMessage] = useState('');
  const [graphData, setGraphData] = useState({ nodes: [], edges: [] });
  const [isLoading, setIsLoading] = useState(false);

  // API基础URL
  const API_BASE_URL = 'http://localhost:8000';

  // 清理状态
  const resetAnalysis = () => {
    setTaskId(null);
    setAnalysisStatus('idle');
    setProgress(0);
    setStatusMessage('');
    setGraphData({ nodes: [], edges: [] });
    setIsLoading(false);
  };

  // 启动文本分析
  const startAnalysis = async () => {
    if (!inputText.trim()) {
      alert('请输入要分析的文本');
      return;
    }

    try {
      setIsLoading(true);
      setAnalysisStatus('pending');
      setStatusMessage('正在创建分析任务...');
      
      console.log('开始分析，文本长度:', inputText.length);

      // 调用启动分析API
      const response = await fetch(`${API_BASE_URL}/api/start-analysis`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text: inputText
        })
      });

      if (!response.ok) {
        throw new Error(`API请求失败: ${response.status}`);
      }

      const data = await response.json();
      console.log('任务创建成功:', data);
      
      setTaskId(data.task_id);
      setAnalysisStatus('processing');
      setStatusMessage('任务已创建，开始处理...');
      
    } catch (error) {
      console.error('启动分析失败:', error);
      setAnalysisStatus('failed');
      setStatusMessage(`分析启动失败: ${error.message}`);
      setIsLoading(false);
    }
  };

  // 轮询任务状态
  useEffect(() => {
    if (!taskId || analysisStatus !== 'processing') return;

    const pollStatus = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/analysis-status/${taskId}`);
        
        if (!response.ok) {
          throw new Error(`状态查询失败: ${response.status}`);
        }

        const statusData = await response.json();
        console.log('状态更新:', statusData);
        
        setProgress(statusData.progress || 0);
        setStatusMessage(statusData.message || '');

        if (statusData.status === 'COMPLETED') {
          setAnalysisStatus('completed');
          setStatusMessage('分析完成，正在获取图谱数据...');
          // 获取图谱数据
          await fetchGraphData(taskId);
        } else if (statusData.status === 'FAILED') {
          setAnalysisStatus('failed');
          setStatusMessage(`分析失败: ${statusData.error || '未知错误'}`);
          setIsLoading(false);
        }
        
      } catch (error) {
        console.error('状态查询失败:', error);
        setAnalysisStatus('failed');
        setStatusMessage(`状态查询失败: ${error.message}`);
        setIsLoading(false);
      }
    };

    // 立即查询一次，然后每2秒查询一次
    pollStatus();
    const interval = setInterval(pollStatus, 2000);

    return () => clearInterval(interval);
  }, [taskId, analysisStatus]);

  // 获取图谱数据
  const fetchGraphData = async (currentTaskId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/graph-data/${currentTaskId}`);
      
      if (!response.ok) {
        throw new Error(`图谱数据获取失败: ${response.status}`);
      }

      const data = await response.json();
      console.log('图谱数据获取成功:', data);
      
      setGraphData({
        nodes: data.nodes || [],
        edges: data.edges || []
      });
      
      setStatusMessage(`图谱生成完成！包含 ${data.nodes?.length || 0} 个节点和 ${data.edges?.length || 0} 个关系`);
      setIsLoading(false);
      
    } catch (error) {
      console.error('图谱数据获取失败:', error);
      setStatusMessage(`图谱数据获取失败: ${error.message}`);
      setIsLoading(false);
    }
  };

  // 示例文本
  const sampleTexts = [
    {
      title: "人工智能基础",
      content: "人工智能（Artificial Intelligence, AI）是计算机科学的一个分支，旨在创建能够执行通常需要人类智能的任务的系统。机器学习是人工智能的一个重要子领域，通过算法让计算机从数据中学习。深度学习是机器学习的一个分支，使用神经网络来模拟人脑的工作方式。"
    },
    {
      title: "科技发展",
      content: "OpenAI是一家专注于人工智能研究的公司，开发了GPT系列模型。GPT是生成式预训练Transformer模型，能够理解和生成自然语言文本。ChatGPT基于GPT模型，专门针对对话场景进行了优化。"
    },
    {
      title: "企业管理",
      content: "企业管理包括战略规划、组织结构、人力资源管理、财务管理、市场营销等多个方面。现代企业需要建立完善的管理体系，通过科学的管理方法提高效率和竞争力。"
    }
  ];

  // 使用示例文本
  const useSampleText = (content) => {
    setInputText(content);
    resetAnalysis();
  };

  return (
    <div className="analysis-page">
      {/* 左侧输入面板 */}
      <div className="input-panel">
        <div className="panel-header">
          <h2>📝 文本输入</h2>
          <p>输入您想要分析的文本内容，我们将为您生成知识图谱</p>
        </div>

        <div className="textarea-container">
          <textarea
            className="text-input"
            placeholder="在此处粘贴您的长文本...&#10;&#10;例如：&#10;• 学术论文段落&#10;• 新闻文章&#10;• 技术文档&#10;• 企业介绍&#10;• 产品描述&#10;&#10;系统将自动提取关键概念并分析它们之间的关系。"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            disabled={isLoading}
          />
          <div className="text-info">
            字符数: {inputText.length} / 50000
          </div>
        </div>

        <div className="sample-texts">
          <h4>💡 示例文本:</h4>
          <div className="sample-buttons">
            {sampleTexts.map((sample, index) => (
              <button
                key={index}
                className="sample-button"
                onClick={() => useSampleText(sample.content)}
                disabled={isLoading}
              >
                {sample.title}
              </button>
            ))}
          </div>
        </div>

        <div className="action-container">
          <button
            className={`analyze-button ${isLoading ? 'loading' : ''}`}
            onClick={startAnalysis}
            disabled={!inputText.trim() || isLoading}
          >
            {isLoading ? '🔄 分析中...' : '🚀 生成知识图谱'}
          </button>
          
          {(analysisStatus !== 'idle' && taskId) && (
            <button
              className="reset-button"
              onClick={resetAnalysis}
              disabled={isLoading}
            >
              🔄 重新开始
            </button>
          )}
        </div>

        {/* 状态显示 */}
        {analysisStatus !== 'idle' && (
          <div className="status-container">
            <div className="status-header">
              <span className={`status-indicator ${analysisStatus}`}>
                {analysisStatus === 'pending' && '⏳'}
                {analysisStatus === 'processing' && '⚙️'}
                {analysisStatus === 'completed' && '✅'}
                {analysisStatus === 'failed' && '❌'}
              </span>
              <span className="status-text">
                {analysisStatus === 'pending' && '准备中'}
                {analysisStatus === 'processing' && '处理中'}
                {analysisStatus === 'completed' && '已完成'}
                {analysisStatus === 'failed' && '失败'}
              </span>
            </div>
            
            {analysisStatus === 'processing' && (
              <div className="progress-container">
                <div className="progress-bar">
                  <div 
                    className="progress-fill" 
                    style={{ width: `${progress}%` }}
                  ></div>
                </div>
                <div className="progress-text">{progress}%</div>
              </div>
            )}
            
            <div className="status-message">{statusMessage}</div>
            
            {taskId && (
              <div className="task-info">
                任务ID: <code>{taskId.slice(0, 8)}...</code>
              </div>
            )}
          </div>
        )}
      </div>

      {/* 右侧图谱面板 */}
      <div className="graph-panel">
        <div className="panel-header">
          <h2>🧠 知识图谱</h2>
          <p>
            {analysisStatus === 'idle' && '分析结果将在此处展示'}
            {analysisStatus === 'pending' && '正在准备图谱生成...'}
            {analysisStatus === 'processing' && '正在构建知识图谱...'}
            {analysisStatus === 'completed' && `图谱包含 ${graphData.nodes.length} 个概念节点`}
            {analysisStatus === 'failed' && '图谱生成失败'}
          </p>
        </div>

        <div className="graph-container">
          {analysisStatus === 'idle' && (
            <div className="welcome-message">
              <div className="welcome-icon">🎯</div>
              <h3>欢迎使用知识图谱分析系统</h3>
              <p>在左侧输入文本，点击"生成知识图谱"开始分析</p>
              <div className="features">
                <div className="feature">
                  <span className="feature-icon">🔍</span>
                  <span>智能概念提取</span>
                </div>
                <div className="feature">
                  <span className="feature-icon">🔗</span>
                  <span>关系识别分析</span>
                </div>
                <div className="feature">
                  <span className="feature-icon">🎮</span>
                  <span>3D交互式展示</span>
                </div>
              </div>
            </div>
          )}

          {(analysisStatus === 'pending' || analysisStatus === 'processing') && (
            <div className="processing-message">
              <div className="spinner"></div>
              <h3>正在生成知识图谱</h3>
              <p>{statusMessage}</p>
              {progress > 0 && (
                <div className="mini-progress">
                  <div className="mini-progress-bar" style={{ width: `${progress}%` }}></div>
                </div>
              )}
            </div>
          )}

          {analysisStatus === 'completed' && graphData.nodes.length > 0 && (
            <div className="graph-canvas-container">
              <GraphCanvas
                nodes={graphData.nodes}
                edges={graphData.edges}
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
                onNodeContextMenu={(node) => {
                  const info = `节点: ${node.label}\nID: ${node.id}\n类型: ${node.type || 'concept'}`;
                  if (node.source_sentence) {
                    info += `\n来源: ${node.source_sentence}`;
                  }
                  alert(info);
                }}
                onCanvasClick={() => {
                  console.log('点击画布');
                }}
              />
              
              {/* 图谱控制信息 */}
              <div className="graph-controls-info">
                <div className="control-tip">
                  <span>🖱️ 左键拖拽旋转</span>
                  <span>🔍 滚轮缩放</span>
                  <span>👆 右键查看详情</span>
                </div>
              </div>
            </div>
          )}

          {analysisStatus === 'failed' && (
            <div className="error-message">
              <div className="error-icon">⚠️</div>
              <h3>图谱生成失败</h3>
              <p>{statusMessage}</p>
              <button className="retry-button" onClick={resetAnalysis}>
                🔄 重试
              </button>
            </div>
          )}

          {analysisStatus === 'completed' && graphData.nodes.length === 0 && (
            <div className="empty-message">
              <div className="empty-icon">📊</div>
              <h3>暂无图谱数据</h3>
              <p>未能从文本中提取到足够的概念信息</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AnalysisPage; 