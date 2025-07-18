"""
文本解构智能体 (Text Deconstruction Agent)

负责将输入文本进行预处理、分段、清洗和结构化，为后续的实体关系抽取做准备。
"""

import autogen
from typing import Dict, List, Any, Optional
import logging
import re
from tools.text_processing import TextProcessor

logger = logging.getLogger(__name__)


class TextDeconstructionAgent(autogen.AssistantAgent):
    """
    文本解构智能体
    
    职责:
    - 文本预处理和清洗
    - 文本分段和结构化
    - 识别文本中的关键结构元素
    - 为后续处理准备标准化的文本格式
    """
    
    def __init__(
        self,
        name: str = "TextDeconstructionAgent",
        system_message: Optional[str] = None,
        **kwargs
    ):
        if system_message is None:
            system_message = self._get_default_system_message()
        
        super().__init__(
            name=name,
            system_message=system_message,
            **kwargs
        )
        
        self.text_processor = TextProcessor()
        self.processed_segments = []
    
    def _get_default_system_message(self) -> str:
        """获取默认的系统消息"""
        return """你是一位文本解构专家，专门负责文本的预处理和结构化。

你的主要职责包括:
1. 对输入文本进行清洗，去除噪声和无关信息
2. 将长文本分解为合理的段落和句子
3. 识别文本中的结构化元素（如标题、列表、表格等）
4. 标准化文本格式，为后续的NLP处理做准备
5. 保持文本的语义完整性和上下文关系

请确保处理后的文本保持原有的语义信息，同时具有良好的结构化特征。"""
    
    def deconstruct_text(self, raw_text: str) -> Dict[str, Any]:
        """
        解构文本的主要方法
        
        Args:
            raw_text: 原始输入文本
            
        Returns:
            解构后的文本结构
        """
        try:
            logger.info("开始文本解构处理...")
            
            # 文本清洗
            cleaned_text = self._clean_text(raw_text)
            
            # 文本分段
            segments = self._segment_text(cleaned_text)
            
            # 结构识别
            structure = self._identify_structure(segments)
            
            # 语义单元划分
            semantic_units = self._create_semantic_units(segments)
            
            result = {
                "original_text": raw_text,
                "cleaned_text": cleaned_text,
                "segments": segments,
                "structure": structure,
                "semantic_units": semantic_units,
                "metadata": {
                    "total_length": len(raw_text),
                    "cleaned_length": len(cleaned_text),
                    "segment_count": len(segments),
                    "processing_agent": self.name
                }
            }
            
            self.processed_segments = segments
            logger.info(f"文本解构完成，共生成 {len(segments)} 个段落")
            
            return result
            
        except Exception as e:
            logger.error(f"文本解构过程中发生错误: {e}")
            raise
    
    def _clean_text(self, text: str) -> str:
        """
        清洗文本
        
        Args:
            text: 待清洗的文本
            
        Returns:
            清洗后的文本
        """
        # 去除多余的空白字符
        cleaned = re.sub(r'\s+', ' ', text.strip())
        
        # 去除特殊字符（保留基本标点）
        cleaned = re.sub(r'[^\w\s\u4e00-\u9fff.,!?;:()\[\]{}""\'\'-]', '', cleaned)
        
        # 规范化标点符号
        cleaned = re.sub(r'[。！？；]', '.', cleaned)
        cleaned = re.sub(r'[，、]', ',', cleaned)
        
        return cleaned
    
    def _segment_text(self, text: str) -> List[str]:
        """
        文本分段
        
        Args:
            text: 待分段的文本
            
        Returns:
            分段后的文本列表
        """
        # 基于句号分割
        sentences = re.split(r'[.!?]+', text)
        
        # 过滤空字符串和过短的句子
        segments = [s.strip() for s in sentences if len(s.strip()) > 10]
        
        # 合并过短的段落
        merged_segments = []
        current_segment = ""
        
        for segment in segments:
            if len(current_segment + segment) < 200:
                current_segment += segment + " "
            else:
                if current_segment:
                    merged_segments.append(current_segment.strip())
                current_segment = segment + " "
        
        if current_segment:
            merged_segments.append(current_segment.strip())
        
        return merged_segments
    
    def _identify_structure(self, segments: List[str]) -> Dict[str, Any]:
        """
        识别文本结构
        
        Args:
            segments: 文本段落列表
            
        Returns:
            文本结构信息
        """
        structure = {
            "document_type": "general",
            "has_title": False,
            "has_sections": False,
            "has_lists": False,
            "paragraph_count": len(segments),
            "sections": []
        }
        
        # 简单的结构识别逻辑
        for i, segment in enumerate(segments):
            if len(segment) < 50 and i == 0:
                structure["has_title"] = True
                structure["title"] = segment
            
            if re.search(r'^\d+[.\s]', segment) or re.search(r'^[一二三四五六七八九十][、.]', segment):
                structure["has_lists"] = True
        
        return structure
    
    def _create_semantic_units(self, segments: List[str]) -> List[Dict[str, Any]]:
        """
        创建语义单元
        
        Args:
            segments: 文本段落列表
            
        Returns:
            语义单元列表
        """
        semantic_units = []
        
        for i, segment in enumerate(segments):
            unit = {
                "id": f"unit_{i+1}",
                "text": segment,
                "position": i,
                "length": len(segment),
                "keywords": self._extract_keywords(segment),
                "sentence_count": len(re.split(r'[,，]', segment))
            }
            semantic_units.append(unit)
        
        return semantic_units
    
    def _extract_keywords(self, text: str) -> List[str]:
        """
        提取关键词（简单实现）
        
        Args:
            text: 输入文本
            
        Returns:
            关键词列表
        """
        # 简单的关键词提取（实际应用中可以使用更复杂的NLP方法）
        words = re.findall(r'\b\w+\b', text)
        # 过滤常见的停用词
        stop_words = {'的', '了', '在', '是', '有', '和', '与', '或', '但', '然而', '因此', '所以'}
        keywords = [word for word in words if len(word) > 1 and word not in stop_words]
        
        # 返回出现频率较高的词（简化实现）
        from collections import Counter
        word_freq = Counter(keywords)
        return [word for word, freq in word_freq.most_common(10)]
    
    def get_processing_statistics(self) -> Dict[str, Any]:
        """
        获取处理统计信息
        
        Returns:
            处理统计信息
        """
        return {
            "agent_name": self.name,
            "processed_segments_count": len(self.processed_segments),
            "total_processed_length": sum(len(seg) for seg in self.processed_segments),
            "average_segment_length": sum(len(seg) for seg in self.processed_segments) / max(len(self.processed_segments), 1)
        } 