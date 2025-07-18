"""
时间解析工具模块

提供时间表达式的识别、解析、标准化和计算功能。
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, date, timedelta
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TimeExpression:
    """时间表达式数据类"""
    original_text: str
    normalized_text: str
    time_type: str
    parsed_datetime: Optional[datetime]
    confidence: float
    start_pos: int
    end_pos: int


class TimeParser:
    """
    时间解析工具类
    
    支持中文和英文的时间表达式识别、解析和标准化
    """
    
    def __init__(self):
        """初始化时间解析器"""
        self.time_patterns = self._load_time_patterns()
        self.base_date = datetime.now()  # 用于相对时间计算的基准日期
    
    def _load_time_patterns(self) -> Dict[str, List[str]]:
        """加载时间表达式模式"""
        return {
            # 绝对日期
            "absolute_date": [
                r'(\d{4})年(\d{1,2})月(\d{1,2})日',
                r'(\d{4})-(\d{1,2})-(\d{1,2})',
                r'(\d{1,2})/(\d{1,2})/(\d{4})',
                r'(\d{4})\.(\d{1,2})\.(\d{1,2})',
                r'(\d{1,2})月(\d{1,2})日',
                r'(\d{1,2})-(\d{1,2})'
            ],
            
            # 年月
            "year_month": [
                r'(\d{4})年(\d{1,2})月',
                r'(\d{4})-(\d{1,2})',
                r'(\d{1,2})/(\d{4})',
                r'(\d{4})\.(\d{1,2})'
            ],
            
            # 年份
            "year": [
                r'(\d{4})年',
                r'公元(\d{4})年',
                r'(\d{4})',
                r'二〇\d{2}年',
                r'一九\d{2}年'
            ],
            
            # 相对时间
            "relative_time": [
                r'今天|今日',
                r'昨天|昨日',
                r'明天|明日',
                r'前天',
                r'后天',
                r'大前天',
                r'大后天',
                r'上周|上星期',
                r'下周|下星期',
                r'这周|这星期|本周|本星期',
                r'上月|上个月',
                r'下月|下个月',
                r'这月|这个月|本月',
                r'去年|上年',
                r'明年|下年',
                r'今年|本年'
            ],
            
            # 时间段
            "duration": [
                r'(\d+)年',
                r'(\d+)个月',
                r'(\d+)月',
                r'(\d+)天',
                r'(\d+)日',
                r'(\d+)小时',
                r'(\d+)分钟',
                r'(\d+)秒',
                r'(\d+)周',
                r'(\d+)星期',
                r'半年',
                r'一年',
                r'两年',
                r'三年'
            ],
            
            # 时间点
            "time_point": [
                r'(\d{1,2}):(\d{1,2}):(\d{1,2})',
                r'(\d{1,2}):(\d{1,2})',
                r'(\d{1,2})点(\d{1,2})分',
                r'(\d{1,2})时(\d{1,2})分',
                r'上午(\d{1,2})点',
                r'下午(\d{1,2})点',
                r'晚上(\d{1,2})点',
                r'凌晨(\d{1,2})点',
                r'中午',
                r'午夜',
                r'黎明',
                r'傍晚'
            ],
            
            # 季节和时期
            "season_period": [
                r'春天|春季',
                r'夏天|夏季',
                r'秋天|秋季|秋',
                r'冬天|冬季|冬',
                r'上半年',
                r'下半年',
                r'第一季度|一季度',
                r'第二季度|二季度',
                r'第三季度|三季度',
                r'第四季度|四季度',
                r'年初',
                r'年中',
                r'年末|年底'
            ],
            
            # 朝代和历史时期
            "dynasty": [
                r'春秋时期|春秋',
                r'战国时期|战国',
                r'秦朝|秦代',
                r'汉朝|汉代',
                r'三国时期|三国',
                r'晋朝|晋代',
                r'南北朝',
                r'隋朝|隋代',
                r'唐朝|唐代',
                r'宋朝|宋代',
                r'元朝|元代',
                r'明朝|明代',
                r'清朝|清代',
                r'民国时期|民国',
                r'近代',
                r'现代',
                r'古代'
            ],
            
            # 世纪和年代
            "century_decade": [
                r'(\d+)世纪',
                r'(\d+)年代',
                r'二十一世纪',
                r'二十世纪',
                r'十九世纪',
                r'八十年代',
                r'九十年代',
                r'新世纪'
            ]
        }
    
    def parse_time_expressions(self, text: str) -> List[TimeExpression]:
        """
        解析文本中的时间表达式
        
        Args:
            text: 输入文本
            
        Returns:
            时间表达式列表
        """
        time_expressions = []
        
        for time_type, patterns in self.time_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    time_expr = self._create_time_expression(
                        match, time_type, text
                    )
                    if time_expr:
                        time_expressions.append(time_expr)
        
        # 去重和排序
        time_expressions = self._deduplicate_expressions(time_expressions)
        time_expressions.sort(key=lambda x: x.start_pos)
        
        return time_expressions
    
    def _create_time_expression(self, match: re.Match, time_type: str, text: str) -> Optional[TimeExpression]:
        """
        创建时间表达式对象
        
        Args:
            match: 正则匹配对象
            time_type: 时间类型
            text: 原始文本
            
        Returns:
            时间表达式对象
        """
        original_text = match.group()
        start_pos = match.start()
        end_pos = match.end()
        
        # 标准化和解析
        normalized_text = self._normalize_time_text(original_text, time_type)
        parsed_datetime = self._parse_datetime(original_text, time_type, match)
        confidence = self._calculate_confidence(original_text, time_type, parsed_datetime)
        
        return TimeExpression(
            original_text=original_text,
            normalized_text=normalized_text,
            time_type=time_type,
            parsed_datetime=parsed_datetime,
            confidence=confidence,
            start_pos=start_pos,
            end_pos=end_pos
        )
    
    def _normalize_time_text(self, text: str, time_type: str) -> str:
        """标准化时间文本"""
        text = text.strip()
        
        # 统一中文数字
        chinese_numbers = {
            '一': '1', '二': '2', '三': '3', '四': '4', '五': '5',
            '六': '6', '七': '7', '八': '8', '九': '9', '十': '10',
            '零': '0', '〇': '0'
        }
        
        for chinese, digit in chinese_numbers.items():
            text = text.replace(chinese, digit)
        
        # 处理特殊表达式
        if time_type == "relative_time":
            relative_mappings = {
                '今天': '今日',
                '昨天': '昨日',
                '明天': '明日',
                '上周': '上星期',
                '下周': '下星期',
                '本周': '这星期',
                '上月': '上个月',
                '下月': '下个月',
                '本月': '这个月'
            }
            for original, normalized in relative_mappings.items():
                if original in text:
                    text = normalized
        
        return text
    
    def _parse_datetime(self, text: str, time_type: str, match: re.Match) -> Optional[datetime]:
        """
        解析为datetime对象
        
        Args:
            text: 时间文本
            time_type: 时间类型
            match: 正则匹配对象
            
        Returns:
            解析后的datetime对象
        """
        try:
            if time_type == "absolute_date":
                return self._parse_absolute_date(text, match)
            elif time_type == "year_month":
                return self._parse_year_month(text, match)
            elif time_type == "year":
                return self._parse_year(text, match)
            elif time_type == "relative_time":
                return self._parse_relative_time(text)
            elif time_type == "time_point":
                return self._parse_time_point(text, match)
            elif time_type == "season_period":
                return self._parse_season_period(text)
            elif time_type == "dynasty":
                return self._parse_dynasty(text)
            elif time_type == "century_decade":
                return self._parse_century_decade(text, match)
            else:
                return None
                
        except Exception as e:
            logger.debug(f"Failed to parse datetime for '{text}': {e}")
            return None
    
    def _parse_absolute_date(self, text: str, match: re.Match) -> Optional[datetime]:
        """解析绝对日期"""
        groups = match.groups()
        
        # 处理不同的日期格式
        if '年' in text and '月' in text and '日' in text:
            # 中文格式：2023年5月15日
            year, month, day = groups
            return datetime(int(year), int(month), int(day))
        
        elif '-' in text and len(groups) == 3:
            # ISO格式：2023-05-15
            year, month, day = groups
            return datetime(int(year), int(month), int(day))
        
        elif '/' in text:
            # 美式格式：05/15/2023 或 15/05/2023
            if len(groups[2]) == 4:  # MM/DD/YYYY
                month, day, year = groups
            else:  # DD/MM/YYYY
                day, month, year = groups
            return datetime(int(year), int(month), int(day))
        
        elif '月' in text and '日' in text:
            # 当年的月日：5月15日
            month, day = groups
            return datetime(self.base_date.year, int(month), int(day))
        
        return None
    
    def _parse_year_month(self, text: str, match: re.Match) -> Optional[datetime]:
        """解析年月"""
        groups = match.groups()
        
        if '年' in text and '月' in text:
            year, month = groups
            return datetime(int(year), int(month), 1)
        elif '-' in text:
            year, month = groups
            return datetime(int(year), int(month), 1)
        
        return None
    
    def _parse_year(self, text: str, match: re.Match) -> Optional[datetime]:
        """解析年份"""
        groups = match.groups()
        
        if groups:
            year = groups[0]
            return datetime(int(year), 1, 1)
        
        # 处理中文年份
        if '年' in text:
            year_str = text.replace('年', '').replace('公元', '')
            if year_str.isdigit():
                return datetime(int(year_str), 1, 1)
        
        return None
    
    def _parse_relative_time(self, text: str) -> Optional[datetime]:
        """解析相对时间"""
        base = self.base_date
        
        relative_mappings = {
            '今天': timedelta(days=0),
            '今日': timedelta(days=0),
            '昨天': timedelta(days=-1),
            '昨日': timedelta(days=-1),
            '明天': timedelta(days=1),
            '明日': timedelta(days=1),
            '前天': timedelta(days=-2),
            '后天': timedelta(days=2),
            '大前天': timedelta(days=-3),
            '大后天': timedelta(days=3),
            '上周': timedelta(weeks=-1),
            '上星期': timedelta(weeks=-1),
            '下周': timedelta(weeks=1),
            '下星期': timedelta(weeks=1),
            '这周': timedelta(days=0),
            '这星期': timedelta(days=0),
            '本周': timedelta(days=0),
            '本星期': timedelta(days=0),
            '去年': timedelta(days=-365),
            '上年': timedelta(days=-365),
            '明年': timedelta(days=365),
            '下年': timedelta(days=365),
            '今年': timedelta(days=0),
            '本年': timedelta(days=0)
        }
        
        for key, delta in relative_mappings.items():
            if key in text:
                result = base + delta
                return result.replace(hour=0, minute=0, second=0, microsecond=0)
        
        return None
    
    def _parse_time_point(self, text: str, match: re.Match) -> Optional[datetime]:
        """解析时间点"""
        groups = match.groups()
        base_date = self.base_date.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # 处理 HH:MM:SS 格式
        if len(groups) == 3 and all(g for g in groups):
            hour, minute, second = map(int, groups)
            return base_date.replace(hour=hour, minute=minute, second=second)
        
        # 处理 HH:MM 格式
        elif len(groups) == 2 and all(g for g in groups):
            hour, minute = map(int, groups)
            return base_date.replace(hour=hour, minute=minute)
        
        # 处理中文时间格式
        if '点' in text:
            if '上午' in text:
                hour = int(re.search(r'(\d+)', text).group(1))
                return base_date.replace(hour=hour)
            elif '下午' in text:
                hour = int(re.search(r'(\d+)', text).group(1))
                hour = hour + 12 if hour < 12 else hour
                return base_date.replace(hour=hour)
            elif '晚上' in text:
                hour = int(re.search(r'(\d+)', text).group(1))
                hour = hour + 12 if hour < 12 else hour
                return base_date.replace(hour=hour)
            elif '凌晨' in text:
                hour = int(re.search(r'(\d+)', text).group(1))
                return base_date.replace(hour=hour)
        
        # 处理特殊时间点
        special_times = {
            '中午': 12,
            '午夜': 0,
            '黎明': 6,
            '傍晚': 18
        }
        
        for key, hour in special_times.items():
            if key in text:
                return base_date.replace(hour=hour)
        
        return None
    
    def _parse_season_period(self, text: str) -> Optional[datetime]:
        """解析季节和时期"""
        year = self.base_date.year
        
        season_mappings = {
            '春天': (3, 1),
            '春季': (3, 1),
            '夏天': (6, 1),
            '夏季': (6, 1),
            '秋天': (9, 1),
            '秋季': (9, 1),
            '秋': (9, 1),
            '冬天': (12, 1),
            '冬季': (12, 1),
            '冬': (12, 1),
            '上半年': (1, 1),
            '下半年': (7, 1),
            '第一季度': (1, 1),
            '一季度': (1, 1),
            '第二季度': (4, 1),
            '二季度': (4, 1),
            '第三季度': (7, 1),
            '三季度': (7, 1),
            '第四季度': (10, 1),
            '四季度': (10, 1),
            '年初': (1, 1),
            '年中': (6, 1),
            '年末': (12, 1),
            '年底': (12, 1)
        }
        
        for key, (month, day) in season_mappings.items():
            if key in text:
                return datetime(year, month, day)
        
        return None
    
    def _parse_dynasty(self, text: str) -> Optional[datetime]:
        """解析朝代（返回朝代的大致起始年份）"""
        dynasty_mappings = {
            '春秋': 770,
            '战国': 475,
            '秦朝': 221,
            '秦代': 221,
            '汉朝': 206,
            '汉代': 206,
            '三国': 220,
            '晋朝': 266,
            '晋代': 266,
            '南北朝': 420,
            '隋朝': 581,
            '隋代': 581,
            '唐朝': 618,
            '唐代': 618,
            '宋朝': 960,
            '宋代': 960,
            '元朝': 1271,
            '元代': 1271,
            '明朝': 1368,
            '明代': 1368,
            '清朝': 1644,
            '清代': 1644,
            '民国': 1912
        }
        
        for key, year in dynasty_mappings.items():
            if key in text:
                return datetime(year, 1, 1)
        
        return None
    
    def _parse_century_decade(self, text: str, match: re.Match) -> Optional[datetime]:
        """解析世纪和年代"""
        groups = match.groups()
        
        if '世纪' in text:
            if groups and groups[0].isdigit():
                century = int(groups[0])
                year = (century - 1) * 100 + 1
                return datetime(year, 1, 1)
            elif '二十一世纪' in text:
                return datetime(2001, 1, 1)
            elif '二十世纪' in text:
                return datetime(1901, 1, 1)
            elif '十九世纪' in text:
                return datetime(1801, 1, 1)
        
        elif '年代' in text:
            if groups and groups[0].isdigit():
                decade = int(groups[0])
                # 假设是19xx或20xx年代
                if decade < 50:
                    year = 2000 + decade
                else:
                    year = 1900 + decade
                return datetime(year, 1, 1)
        
        return None
    
    def _calculate_confidence(self, text: str, time_type: str, parsed_datetime: Optional[datetime]) -> float:
        """计算置信度"""
        base_confidence = 0.5
        
        # 根据时间类型调整置信度
        type_confidence = {
            "absolute_date": 0.9,
            "year_month": 0.8,
            "year": 0.7,
            "relative_time": 0.8,
            "time_point": 0.7,
            "season_period": 0.6,
            "dynasty": 0.5,
            "century_decade": 0.6,
            "duration": 0.7
        }
        
        confidence = type_confidence.get(time_type, base_confidence)
        
        # 如果成功解析为datetime，增加置信度
        if parsed_datetime:
            confidence += 0.2
        
        # 根据文本长度和复杂度调整
        if len(text) > 10:
            confidence += 0.1
        
        # 包含具体数字的表达式置信度更高
        if re.search(r'\d', text):
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _deduplicate_expressions(self, expressions: List[TimeExpression]) -> List[TimeExpression]:
        """去重时间表达式"""
        if not expressions:
            return []
        
        # 按位置排序
        expressions.sort(key=lambda x: (x.start_pos, x.end_pos))
        
        deduplicated = []
        for expr in expressions:
            # 检查是否与已有表达式重叠
            overlapped = False
            for existing in deduplicated:
                if (expr.start_pos < existing.end_pos and 
                    expr.end_pos > existing.start_pos):
                    # 有重叠，保留置信度更高的
                    if expr.confidence > existing.confidence:
                        deduplicated.remove(existing)
                        deduplicated.append(expr)
                    overlapped = True
                    break
            
            if not overlapped:
                deduplicated.append(expr)
        
        return deduplicated
    
    def calculate_time_span(self, expressions: List[TimeExpression]) -> Optional[Dict[str, Any]]:
        """
        计算时间跨度
        
        Args:
            expressions: 时间表达式列表
            
        Returns:
            时间跨度信息
        """
        valid_datetimes = [
            expr.parsed_datetime for expr in expressions 
            if expr.parsed_datetime
        ]
        
        if len(valid_datetimes) < 2:
            return None
        
        earliest = min(valid_datetimes)
        latest = max(valid_datetimes)
        span = latest - earliest
        
        return {
            "earliest": earliest,
            "latest": latest,
            "span_days": span.days,
            "span_years": span.days / 365.25,
            "total_expressions": len(expressions),
            "parsed_expressions": len(valid_datetimes)
        }
    
    def get_time_statistics(self, expressions: List[TimeExpression]) -> Dict[str, Any]:
        """
        获取时间表达式统计信息
        
        Args:
            expressions: 时间表达式列表
            
        Returns:
            统计信息字典
        """
        if not expressions:
            return {
                "total_count": 0,
                "parsed_count": 0,
                "type_distribution": {},
                "average_confidence": 0.0
            }
        
        # 类型分布
        type_distribution = {}
        for expr in expressions:
            type_distribution[expr.time_type] = type_distribution.get(expr.time_type, 0) + 1
        
        # 解析成功率
        parsed_count = len([expr for expr in expressions if expr.parsed_datetime])
        
        # 平均置信度
        average_confidence = sum(expr.confidence for expr in expressions) / len(expressions)
        
        return {
            "total_count": len(expressions),
            "parsed_count": parsed_count,
            "parse_success_rate": parsed_count / len(expressions),
            "type_distribution": type_distribution,
            "average_confidence": average_confidence,
            "time_span": self.calculate_time_span(expressions)
        }
    
    def format_time_expression(self, expression: TimeExpression, format_type: str = "iso") -> str:
        """
        格式化时间表达式
        
        Args:
            expression: 时间表达式对象
            format_type: 格式类型 ("iso", "chinese", "english")
            
        Returns:
            格式化后的字符串
        """
        if not expression.parsed_datetime:
            return expression.normalized_text
        
        dt = expression.parsed_datetime
        
        if format_type == "iso":
            return dt.isoformat()
        elif format_type == "chinese":
            return f"{dt.year}年{dt.month}月{dt.day}日"
        elif format_type == "english":
            return dt.strftime("%B %d, %Y")
        else:
            return str(dt) 