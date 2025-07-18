import React, { useState, useEffect } from 'react';
import { GraphCanvas, darkTheme } from 'reagraph';
import KnowledgeGraph from './KnowledgeGraph';
import './AnalysisPage.css';

const AnalysisPage = () => {
  // 按照要求的状态管理结构
  const [inputText, setInputText] = useState('');
  const [graphData, setGraphData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  // 额外的状态管理用于增强用户体验
  const [taskId, setTaskId] = useState(null);
  const [progress, setProgress] = useState(0);
  const [statusMessage, setStatusMessage] = useState('');
  const [currentInterval, setCurrentInterval] = useState(null);

  // API基础URL
  const API_BASE_URL = 'http://localhost:8000';

  // 清理轮询定时器
  const clearPolling = () => {
    if (currentInterval) {
      clearInterval(currentInterval);
      setCurrentInterval(null);
    }
  };

  // 组件卸载时清理定时器
  useEffect(() => {
    return () => {
      clearPolling();
    };
  }, []);

  // 主要的分析处理函数 - 按照要求命名为 handleAnalysis
  const handleAnalysis = async () => {
    if (!inputText.trim()) {
      setError('请输入要分析的文本');
      return;
    }

    try {
      // a. 设置loading状态，清空旧数据
      setIsLoading(true);
      setGraphData(null);
      setError(null);
      setProgress(0);
      setStatusMessage('正在创建分析任务...');
      
      console.log('🚀 开始分析，文本长度:', inputText.length);

      // b. 向后端发送POST请求启动分析
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
        throw new Error(`API请求失败: ${response.status} ${response.statusText}`);
      }

      // c. 获取task_id
      const data = await response.json();
      const currentTaskId = data.task_id;
      setTaskId(currentTaskId);
      setStatusMessage('任务已创建，开始处理...');
      
      console.log('📝 任务创建成功，ID:', currentTaskId);

      // d. 设置定时器，每3秒轮询状态
      const intervalId = setInterval(async () => {
        try {
          console.log('🔄 轮询任务状态...');
          const statusResponse = await fetch(`${API_BASE_URL}/api/analysis-status/${currentTaskId}`);
          
          if (!statusResponse.ok) {
            throw new Error(`状态查询失败: ${statusResponse.status}`);
          }

          const statusData = await statusResponse.json();
          console.log('📊 状态更新:', statusData);
          
          // 更新进度和消息
          setProgress(statusData.progress || 0);
          setStatusMessage(statusData.message || '处理中...');

          // e. 检查是否完成
          if (statusData.status === 'COMPLETED') {
            console.log('✅ 分析完成，开始获取图谱数据');
            clearInterval(intervalId);
            setCurrentInterval(null);
            
            // 向 /api/graph-data/{task_id} 发送GET请求
            try {
              setStatusMessage('分析完成，正在获取图谱数据...');
              const graphResponse = await fetch(`${API_BASE_URL}/api/graph-data/${currentTaskId}`);
              
              if (!graphResponse.ok) {
                throw new Error(`图谱数据获取失败: ${graphResponse.status}`);
              }

              const graphData = await graphResponse.json();
              console.log('📈 图谱数据获取成功:', graphData);
              
              // 更新graphData状态 - 现在包含集群信息
              setGraphData({
                nodes: graphData.nodes || [],
                edges: graphData.edges || [],
                clusters: graphData.clusters || {},
                metadata: graphData.metadata || {}
              });
              
              const clusterCount = Object.keys(graphData.clusters || {}).length;
              setStatusMessage(`图谱生成完成！包含 ${graphData.nodes?.length || 0} 个节点、${graphData.edges?.length || 0} 个关系，分为 ${clusterCount} 个集群`);
              setIsLoading(false);
              
            } catch (graphError) {
              console.error('❌ 获取图谱数据失败:', graphError);
              setError(`获取图谱数据失败: ${graphError.message}`);
              setIsLoading(false);
            }
            
          } else if (statusData.status === 'FAILED') {
            // f. 处理失败状态
            console.error('❌ 分析失败:', statusData.error);
            clearInterval(intervalId);
            setCurrentInterval(null);
            setError(`分析失败: ${statusData.error || '未知错误'}`);
            setIsLoading(false);
          }
          
        } catch (pollError) {
          console.error('❌ 轮询失败:', pollError);
          clearInterval(intervalId);
          setCurrentInterval(null);
          setError(`状态查询失败: ${pollError.message}`);
          setIsLoading(false);
        }
      }, 3000); // 每3秒轮询一次
      
      setCurrentInterval(intervalId);
      
    } catch (error) {
      console.error('❌ 启动分析失败:', error);
      setError(`启动分析失败: ${error.message}`);
      setIsLoading(false);
      clearPolling();
    }
  };

  // 重置所有状态
  const resetAnalysis = () => {
    clearPolling();
    setGraphData(null);
    setError(null);
    setIsLoading(false);
    setTaskId(null);
    setProgress(0);
    setStatusMessage('');
    console.log('🔄 分析状态已重置');
  };

  // 示例文本数据
  const sampleTexts = [
    {
      title: "人工智能基础",
      content: "人工智能（Artificial Intelligence, AI）是计算机科学的一个分支，旨在创建能够执行通常需要人类智能的任务的系统。机器学习是人工智能的一个重要子领域，通过算法让计算机从数据中学习。深度学习是机器学习的一个分支，使用神经网络来模拟人脑的工作方式。自然语言处理和计算机视觉是AI的重要应用领域。"
    },
    {
      title: "科技发展",
      content: "OpenAI是一家专注于人工智能研究的公司，开发了GPT系列模型。GPT是生成式预训练Transformer模型，能够理解和生成自然语言文本。ChatGPT基于GPT模型，专门针对对话场景进行了优化。这些技术推动了AI在各个行业的应用和发展。"
    },
    {
      title: "企业管理",
      content: "企业管理包括战略规划、组织结构、人力资源管理、财务管理、市场营销等多个方面。现代企业需要建立完善的管理体系，通过科学的管理方法提高效率和竞争力。数字化转型和创新管理已成为企业发展的关键要素。"
    }
  ];

  // 使用示例文本
  const useSampleText = (content) => {
    setInputText(content);
    resetAnalysis();
  };

  // 检查API连接状态
  const [apiStatus, setApiStatus] = useState('checking');
  
  useEffect(() => {
    const checkApiConnection = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/health`);
        if (response.ok) {
          setApiStatus('connected');
          console.log('✅ API连接正常');
        } else {
          setApiStatus('error');
        }
      } catch (error) {
        setApiStatus('error');
        console.warn('⚠️ API连接失败:', error);
      }
    };
    
    checkApiConnection();
  }, []);

  return (
    <div className="analysis-page">
      {/* 左侧输入面板 */}
      <div className="input-panel">
        <div className="panel-header">
          <h2>📝 文本输入</h2>
          <p>输入您想要分析的文本内容，我们将为您生成集群化的知识图谱</p>
        </div>

        <div className="textarea-container">
          <textarea
            className="text-input"
            placeholder="在此处粘贴您的长文本...&#10;&#10;例如：&#10;• 学术论文段落&#10;• 新闻文章&#10;• 技术文档&#10;• 企业介绍&#10;• 产品描述&#10;&#10;系统将自动提取关键概念并按照语义相似性分为不同集群。"
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
          {/* 3. 条件渲染: 按钮在isLoading时禁用 */}
          <button
            className={`analyze-button ${isLoading ? 'loading' : ''}`}
            onClick={handleAnalysis}
            disabled={!inputText.trim() || isLoading}
          >
            {isLoading ? '🔄 分析中...' : '🚀 生成集群化图谱'}
          </button>
          
          {(taskId || error) && (
            <button
              className="reset-button"
              onClick={resetAnalysis}
              disabled={isLoading}
            >
              🔄 重新开始
            </button>
          )}
        </div>

        {/* 状态显示面板 */}
        {(isLoading || error || graphData) && (
          <div className="status-container">
            <div className="status-header">
              <span className={`status-indicator ${isLoading ? 'processing' : error ? 'failed' : 'completed'}`}>
                {isLoading && '⚙️'}
                {error && '❌'}
                {graphData && !isLoading && !error && '✅'}
              </span>
              <span className="status-text">
                {isLoading && '处理中'}
                {error && '失败'}
                {graphData && !isLoading && !error && '已完成'}
              </span>
            </div>
            
            {isLoading && (
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
            
            <div className="status-message">
              {error && error}
              {!error && statusMessage}
            </div>
            
            {taskId && (
              <div className="task-info">
                任务ID: <code>{taskId.slice(0, 8)}...</code>
              </div>
            )}
          </div>
        )}

        {/* API连接状态 */}
        <div className={`api-status ${apiStatus}`} style={{ 
          position: 'fixed', 
          bottom: '20px', 
          left: '20px',
          padding: '8px 12px',
          borderRadius: '8px',
          fontSize: '12px',
          backgroundColor: 'rgba(0,0,0,0.8)',
          border: `1px solid ${apiStatus === 'connected' ? 'rgba(0,255,136,0.3)' : 'rgba(255,107,107,0.3)'}`,
          color: apiStatus === 'connected' ? '#00FF88' : '#FF6B6B'
        }}>
          {apiStatus === 'checking' && '🔌 检查API连接...'}
          {apiStatus === 'connected' && '🟢 API服务正常'}
          {apiStatus === 'error' && '🔴 API服务离线'}
        </div>
      </div>

      {/* 右侧图谱面板 */}
      <div className="graph-panel">
        <div className="panel-header">
          <h2>🧠 集群化知识图谱</h2>
          <p>
            {/* 3. 条件渲染: 根据状态显示不同描述 */}
            {!isLoading && !error && !graphData && '分析结果将在此处展示'}
            {isLoading && '正在构建集群化知识图谱...'}
            {error && '图谱生成失败'}
            {graphData && !isLoading && !error && 
              `图谱包含 ${graphData.nodes.length} 个概念节点，分为 ${Object.keys(graphData.clusters || {}).length} 个集群`
            }
          </p>
        </div>

        <div className="graph-container">
          {/* 3. 条件渲染: 初始欢迎状态 */}
          {!isLoading && !error && !graphData && (
            <div className="welcome-message">
              <div className="welcome-icon">🎯</div>
              <h3>欢迎使用集群化知识图谱分析系统</h3>
              <p>在左侧输入文本，点击"生成集群化图谱"开始分析</p>
              <div className="features">
                <div className="feature">
                  <span className="feature-icon">🧩</span>
                  <span>智能集群化显示</span>
                </div>
                <div className="feature">
                  <span className="feature-icon">🔍</span>
                  <span>语义相似性分析</span>
                </div>
                <div className="feature">
                  <span className="feature-icon">🎮</span>
                  <span>可切换显示模式</span>
                </div>
              </div>
            </div>
          )}

          {/* 3. 条件渲染: 加载状态 */}
          {isLoading && (
            <div className="processing-message">
              <div className="spinner"></div>
              <h3>正在分析中...</h3>
              <p>{statusMessage}</p>
              {progress > 0 && (
                <div className="mini-progress">
                  <div className="mini-progress-bar" style={{ width: `${progress}%` }}></div>
                </div>
              )}
              <div style={{ marginTop: '20px', fontSize: '14px', color: '#888' }}>
                💡 提示：系统正在进行语义分析和集群化处理
              </div>
            </div>
          )}

          {/* 3. 条件渲染: 如果graphData有数据，渲染集群化KnowledgeGraph组件 */}
          {graphData && graphData.nodes.length > 0 && !isLoading && !error && (
            <KnowledgeGraph graphData={graphData} />
          )}

          {/* 3. 条件渲染: 错误状态 */}
          {error && (
            <div className="error-message">
              <div className="error-icon">⚠️</div>
              <h3>图谱生成失败</h3>
              <p>{error}</p>
              <button className="retry-button" onClick={resetAnalysis}>
                🔄 重试
              </button>
            </div>
          )}

          {/* 3. 条件渲染: 空数据状态 */}
          {graphData && graphData.nodes.length === 0 && !isLoading && !error && (
            <div className="empty-message">
              <div className="empty-icon">📊</div>
              <h3>暂无图谱数据</h3>
              <p>未能从文本中提取到足够的概念信息，请尝试输入更详细的文本内容</p>
              <button className="retry-button" onClick={resetAnalysis}>
                🔄 重新分析
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AnalysisPage; 