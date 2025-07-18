"""
文本处理工具模块

提供各种文本预处理、分析和转换功能，支持知识图谱构建中的文本处理需求。
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from collections import Counter
import jieba
import jieba.posseg as pseg

logger = logging.getLogger(__name__)


class TextProcessor:
    """
    文本处理工具类
    
    提供文本清洗、分词、关键词提取、语言检测等功能
    """
    
    def __init__(self):
        """初始化文本处理器"""
        self.stop_words = self._load_stop_words()
        self._init_jieba()
    
    def _load_stop_words(self) -> set:
        """加载停用词表"""
        # 中文停用词
        chinese_stop_words = {
            '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这', '那', '来', '用', '过', '想', '能', '么', '从', '只', '还', '把', '但', '然而', '因此', '所以', '而且', '然后', '或者', '以及', '以及', '等等'
        }
        
        # 英文停用词
        english_stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'as', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'
        }
        
        return chinese_stop_words.union(english_stop_words)
    
    def _init_jieba(self):
        """初始化jieba分词器"""
        try:
            # 添加自定义词典（可选）
            # jieba.load_userdict("custom_dict.txt")
            
            # 启用HMM模型
            jieba.enable_paddle()  # 启用paddle模式获得更好的分词效果
            logger.info("jieba分词器初始化成功")
        except Exception as e:
            logger.warning(f"jieba分词器初始化部分失败: {e}")
    
    def clean_text(self, text: str, remove_extra_spaces: bool = True, 
                   normalize_punctuation: bool = True, 
                   remove_special_chars: bool = True) -> str:
        """
        清洗文本
        
        Args:
            text: 输入文本
            remove_extra_spaces: 是否移除多余空格
            normalize_punctuation: 是否标准化标点符号
            remove_special_chars: 是否移除特殊字符
            
        Returns:
            清洗后的文本
        """
        if not text:
            return ""
        
        cleaned_text = text
        
        # 移除多余的空白字符
        if remove_extra_spaces:
            cleaned_text = re.sub(r'\s+', ' ', cleaned_text.strip())
        
        # 标准化标点符号
        if normalize_punctuation:
            # 中文标点转换
            cleaned_text = re.sub(r'[。！？；]', '.', cleaned_text)
            cleaned_text = re.sub(r'[，、]', ',', cleaned_text)
            cleaned_text = re.sub(r'[：]', ':', cleaned_text)
            cleaned_text = re.sub(r'[（）]', '()', cleaned_text)
            cleaned_text = re.sub(r'[【】]', '[]', cleaned_text)
            
            # 英文标点标准化
            cleaned_text = re.sub(r'[""'']', '"', cleaned_text)
            cleaned_text = re.sub(r'[–—]', '-', cleaned_text)
        
        # 移除特殊字符（保留基本字符和标点）
        if remove_special_chars:
            # 保留中文字符、英文字符、数字和基本标点
            cleaned_text = re.sub(r'[^\w\s\u4e00-\u9fff.,!?;:()\[\]{}"\'`\-]', '', cleaned_text)
        
        return cleaned_text.strip()
    
    def detect_language(self, text: str) -> str:
        """
        检测文本语言
        
        Args:
            text: 输入文本
            
        Returns:
            语言代码 ('zh' for Chinese, 'en' for English, 'mixed' for mixed)
        """
        if not text:
            return "unknown"
        
        # 统计中文字符
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        # 统计英文字符
        english_chars = len(re.findall(r'[a-zA-Z]', text))
        # 总字符数
        total_chars = chinese_chars + english_chars
        
        if total_chars == 0:
            return "unknown"
        
        chinese_ratio = chinese_chars / total_chars
        english_ratio = english_chars / total_chars
        
        if chinese_ratio > 0.7:
            return "zh"
        elif english_ratio > 0.7:
            return "en"
        elif chinese_ratio > 0.3 and english_ratio > 0.3:
            return "mixed"
        else:
            return "unknown"
    
    def tokenize(self, text: str, use_jieba: bool = True, 
                 include_pos: bool = False) -> List[str] or List[Tuple[str, str]]:
        """
        文本分词
        
        Args:
            text: 输入文本
            use_jieba: 是否使用jieba分词
            include_pos: 是否包含词性标注
            
        Returns:
            分词结果列表
        """
        if not text:
            return []
        
        language = self.detect_language(text)
        
        if language in ['zh', 'mixed'] and use_jieba:
            if include_pos:
                # 使用jieba进行词性标注
                words = list(pseg.cut(text))
                return [(word, pos) for word, pos in words if len(word.strip()) > 0]
            else:
                # 使用jieba分词
                words = list(jieba.cut(text))
                return [word for word in words if len(word.strip()) > 0]
        else:
            # 简单的英文分词
            words = re.findall(r'\b\w+\b', text.lower())
            if include_pos:
                # 简单的词性标注（实际应用中可以使用nltk等工具）
                return [(word, 'UNKNOWN') for word in words]
            else:
                return words
    
    def extract_keywords(self, text: str, top_k: int = 10, 
                        min_word_length: int = 2) -> List[Tuple[str, float]]:
        """
        提取关键词
        
        Args:
            text: 输入文本
            top_k: 返回前k个关键词
            min_word_length: 最小词长度
            
        Returns:
            关键词列表，每个元素为(词, 权重)
        """
        if not text:
            return []
        
        # 分词
        words = self.tokenize(text, use_jieba=True)
        
        # 过滤停用词和短词
        filtered_words = [
            word for word in words 
            if (len(word) >= min_word_length and 
                word.lower() not in self.stop_words and
                not re.match(r'^\d+$', word))  # 过滤纯数字
        ]
        
        if not filtered_words:
            return []
        
        # 计算词频
        word_freq = Counter(filtered_words)
        
        # 计算TF-IDF权重（简化版本）
        total_words = len(filtered_words)
        keywords_with_scores = []
        
        for word, freq in word_freq.items():
            # 简化的TF-IDF计算
            tf = freq / total_words
            # 这里使用简化的权重计算，实际应用中可以使用更复杂的算法
            score = tf * (1 + len(word) * 0.1)  # 给长词更高权重
            keywords_with_scores.append((word, score))
        
        # 按权重排序并返回前k个
        keywords_with_scores.sort(key=lambda x: x[1], reverse=True)
        return keywords_with_scores[:top_k]
    
    def extract_sentences(self, text: str) -> List[str]:
        """
        提取句子
        
        Args:
            text: 输入文本
            
        Returns:
            句子列表
        """
        if not text:
            return []
        
        # 基于标点符号分割句子
        sentences = re.split(r'[.!?。！？；]+', text)
        
        # 清理和过滤句子
        cleaned_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 5:  # 过滤过短的句子
                cleaned_sentences.append(sentence)
        
        return cleaned_sentences
    
    def calculate_text_similarity(self, text1: str, text2: str) -> float:
        """
        计算文本相似度（简化实现）
        
        Args:
            text1: 文本1
            text2: 文本2
            
        Returns:
            相似度分数 (0-1)
        """
        if not text1 or not text2:
            return 0.0
        
        # 分词
        words1 = set(self.tokenize(text1))
        words2 = set(self.tokenize(text2))
        
        if not words1 or not words2:
            return 0.0
        
        # 计算Jaccard相似度
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def extract_entities_simple(self, text: str) -> Dict[str, List[str]]:
        """
        简单的实体识别（基于规则）
        
        Args:
            text: 输入文本
            
        Returns:
            实体字典，键为实体类型，值为实体列表
        """
        entities = {
            'PERSON': [],
            'ORGANIZATION': [],
            'LOCATION': [],
            'DATE': [],
            'NUMBER': [],
            'EMAIL': [],
            'URL': []
        }
        
        # 人名模式（中文）
        person_pattern = r'[\u4e00-\u9fff]{2,4}(?=先生|女士|教授|博士|总裁|经理|主任|局长|同志)'
        entities['PERSON'].extend(re.findall(person_pattern, text))
        
        # 机构名模式
        org_pattern = r'[\u4e00-\u9fff]{3,20}(?:公司|企业|集团|学院|大学|政府|部门|机构|银行|医院)'
        entities['ORGANIZATION'].extend(re.findall(org_pattern, text))
        
        # 地名模式
        location_pattern = r'[\u4e00-\u9fff]{2,10}(?:省|市|县|区|镇|村|路|街|国|州|府)'
        entities['LOCATION'].extend(re.findall(location_pattern, text))
        
        # 日期模式
        date_patterns = [
            r'\d{4}年\d{1,2}月\d{1,2}日',
            r'\d{4}-\d{1,2}-\d{1,2}',
            r'\d{1,2}/\d{1,2}/\d{4}'
        ]
        for pattern in date_patterns:
            entities['DATE'].extend(re.findall(pattern, text))
        
        # 数字模式
        number_pattern = r'\d+(?:\.\d+)?(?:万|千|百|十)?(?:元|人|次|个|项|件|%|％)'
        entities['NUMBER'].extend(re.findall(number_pattern, text))
        
        # 邮箱模式
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        entities['EMAIL'].extend(re.findall(email_pattern, text))
        
        # URL模式
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        entities['URL'].extend(re.findall(url_pattern, text))
        
        # 去重
        for entity_type in entities:
            entities[entity_type] = list(set(entities[entity_type]))
        
        return entities
    
    def normalize_text(self, text: str) -> str:
        """
        文本标准化
        
        Args:
            text: 输入文本
            
        Returns:
            标准化后的文本
        """
        if not text:
            return ""
        
        # 转换为小写（对英文）
        normalized = text.lower()
        
        # 全角转半角
        normalized = self._full_width_to_half_width(normalized)
        
        # 繁体转简体（如果需要的话）
        # normalized = self._traditional_to_simplified(normalized)
        
        return normalized
    
    def _full_width_to_half_width(self, text: str) -> str:
        """全角字符转半角字符"""
        result = ""
        for char in text:
            code = ord(char)
            if code == 0x3000:  # 全角空格
                result += chr(0x0020)
            elif 0xFF01 <= code <= 0xFF5E:  # 全角ASCII字符
                result += chr(code - 0xFEE0)
            else:
                result += char
        return result
    
    def segment_by_length(self, text: str, max_length: int = 500, 
                         overlap: int = 50) -> List[str]:
        """
        按长度分割文本
        
        Args:
            text: 输入文本
            max_length: 最大长度
            overlap: 重叠长度
            
        Returns:
            分割后的文本片段列表
        """
        if not text or len(text) <= max_length:
            return [text] if text else []
        
        segments = []
        start = 0
        
        while start < len(text):
            end = min(start + max_length, len(text))
            segment = text[start:end]
            segments.append(segment)
            
            if end >= len(text):
                break
            
            start = end - overlap
        
        return segments
    
    def get_text_statistics(self, text: str) -> Dict[str, Any]:
        """
        获取文本统计信息
        
        Args:
            text: 输入文本
            
        Returns:
            统计信息字典
        """
        if not text:
            return {
                "total_length": 0,
                "word_count": 0,
                "sentence_count": 0,
                "character_count": 0,
                "language": "unknown"
            }
        
        # 基本统计
        total_length = len(text)
        words = self.tokenize(text)
        word_count = len(words)
        sentences = self.extract_sentences(text)
        sentence_count = len(sentences)
        
        # 字符统计
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        english_chars = len(re.findall(r'[a-zA-Z]', text))
        digit_chars = len(re.findall(r'\d', text))
        
        # 语言检测
        language = self.detect_language(text)
        
        return {
            "total_length": total_length,
            "word_count": word_count,
            "sentence_count": sentence_count,
            "character_count": {
                "chinese": chinese_chars,
                "english": english_chars,
                "digits": digit_chars,
                "total": chinese_chars + english_chars + digit_chars
            },
            "language": language,
            "average_word_length": sum(len(word) for word in words) / max(word_count, 1),
            "average_sentence_length": total_length / max(sentence_count, 1)
        } 