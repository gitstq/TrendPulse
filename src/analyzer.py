"""
AI分析模块
提供情感分析、智能摘要、关键词提取等功能
"""

import re
from typing import List, Optional, Dict, Any
from datetime import datetime

from snownlp import SnowNLP
from loguru import logger

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

from src.models import TrendItemCreate, TrendItemDB, SentimentType
from src.config import AIConfig


class SentimentAnalyzer:
    """情感分析器"""
    
    def __init__(self):
        self.snownlp = SnowNLP
    
    def analyze(self, text: str) -> tuple[SentimentType, float]:
        """
        分析文本情感倾向
        返回: (情感类型, 情感分数)
        """
        try:
            s = self.snownlp(text)
            sentiment_score = s.sentiments  # 0-1之间，越接近1越正面
            
            # 转换为我们的情感类型
            if sentiment_score > 0.6:
                sentiment = SentimentType.POSITIVE
            elif sentiment_score < 0.4:
                sentiment = SentimentType.NEGATIVE
            else:
                sentiment = SentimentType.NEUTRAL
            
            # 标准化分数到 -1 到 1
            normalized_score = (sentiment_score - 0.5) * 2
            
            return sentiment, round(normalized_score, 2)
        except Exception as e:
            logger.warning(f"情感分析失败: {e}")
            return SentimentType.NEUTRAL, 0.0


class KeywordExtractor:
    """关键词提取器"""
    
    # 停用词列表
    STOP_WORDS = {
        "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一", "一个", "上", "也",
        "很", "到", "说", "要", "去", "你", "会", "着", "没有", "看", "好", "自己", "这", "那",
        "这些", "那些", "这个", "那个", "之", "与", "及", "等", "或", "但", "而", "因为", "所以",
        "如果", "虽然", "但是", "然而", "而且", "或者", "还是", "要么", "假如", "假定", "譬如",
        "例如", "比如", "像是", "像", "如", "若", "假设", "假使", "要是", "若是", "倘若", "倘使",
        "万一", "如果", "若是", "只要", "只有", "除非", "无论", "不管", "不论", "尽管", "即使",
        "即便", "哪怕", "尽管", "不管", "无论", "不论", "尽管", "虽然", "虽说", "固然", "尽管",
        "虽说", "虽然", "尽管", "不过", "只是", "但是", "可", "可是", "然而", "而", "不过",
        "只是", "但是", "但", "却", "然而", "不过", "只是", "而", "而且", "并且", "况且", "何况",
        "再说", "再者", "否则", "不然", "要不", "要不然", "要么", "因为", "由于", "因此", "因而",
        "所以", "于是", "从而", "可见", "足见", "以致", "以至于", "以至", "直到", "甚至", "甚而",
        "乃至", "以及", "和", "跟", "同", "与", "而", "或", "或者", "还是", "既", "又", "不但",
        "不仅", "不只", "不光", "不单", "不独", "而且", "并且", "况且", "何况", "再说", "再者",
        "否则", "不然", "要不", "要不然", "要么", "与其", "宁可", "宁愿", "宁肯", "不如", "毋宁",
        "还是", "或者", "要么", "一来", "二来", "一方面", "另一方面", "首先", "其次", "再次",
        "最后", "第一", "第二", "第三", "其一", "其二", "一是", "二是", "三是"
    }
    
    def extract(self, text: str, top_k: int = 5) -> str:
        """
        从文本中提取关键词
        返回: 逗号分隔的关键词字符串
        """
        try:
            s = SnowNLP(text)
            keywords = s.keywords(top_k * 2)  # 多提取一些，过滤后再返回
            
            # 过滤停用词和单字词
            filtered = []
            for kw in keywords:
                if kw not in self.STOP_WORDS and len(kw) >= 2:
                    filtered.append(kw)
                if len(filtered) >= top_k:
                    break
            
            return ",".join(filtered) if filtered else ""
        except Exception as e:
            logger.warning(f"关键词提取失败: {e}")
            return ""


class AISummarizer:
    """AI摘要生成器"""
    
    def __init__(self, config: AIConfig):
        self.config = config
        self.provider = config.provider
        self.api_key = config.api_key
        self.model = config.model
        self.max_length = config.summary_max_length
        
        self.client = None
        self._init_client()
    
    def _init_client(self):
        """初始化AI客户端"""
        if not self.api_key:
            logger.warning("未配置AI API密钥，AI摘要功能将不可用")
            return
        
        if self.provider == "openai" and OPENAI_AVAILABLE:
            self.client = openai.AsyncOpenAI(api_key=self.api_key)
        elif self.provider == "anthropic" and ANTHROPIC_AVAILABLE:
            self.client = anthropic.AsyncAnthropic(api_key=self.api_key)
    
    async def summarize(self, title: str, content: str = "") -> Optional[str]:
        """
        生成文本摘要
        """
        if not self.client:
            return None
        
        try:
            prompt = f"""请为以下热点新闻生成一个简短的摘要（不超过{self.max_length}字）：

标题：{title}

{content if content else ""}

要求：
1. 简洁明了，突出重点
2. 客观陈述，不加入主观评价
3. 只返回摘要内容，不要有任何前缀或说明
"""
            
            if self.provider == "openai":
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "你是一个专业的新闻摘要生成助手。"},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=self.max_length,
                    temperature=0.7
                )
                summary = response.choices[0].message.content.strip()
                
            elif self.provider == "anthropic":
                response = await self.client.messages.create(
                    model=self.model,
                    max_tokens=self.max_length,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                summary = response.content[0].text.strip()
            else:
                return None
            
            return summary[:self.max_length]
            
        except Exception as e:
            logger.error(f"AI摘要生成失败: {e}")
            return None


class TrendAnalyzer:
    """热点分析器"""
    
    def __init__(self, ai_config: Optional[AIConfig] = None):
        self.sentiment_analyzer = SentimentAnalyzer()
        self.keyword_extractor = KeywordExtractor()
        self.ai_summarizer = AISummarizer(ai_config) if ai_config else None
    
    async def analyze_item(self, item: TrendItemCreate) -> Dict[str, Any]:
        """
        分析单个热点条目
        返回包含情感、关键词、摘要的分析结果
        """
        result = {
            "sentiment": SentimentType.NEUTRAL,
            "sentiment_score": 0.0,
            "keywords": "",
            "summary": None
        }
        
        # 情感分析
        sentiment, sentiment_score = self.sentiment_analyzer.analyze(item.title)
        result["sentiment"] = sentiment
        result["sentiment_score"] = sentiment_score
        
        # 关键词提取
        keywords = self.keyword_extractor.extract(item.title)
        result["keywords"] = keywords
        
        # AI摘要（如果启用）
        if self.ai_summarizer and self.ai_summarizer.config.enable_summary:
            summary = await self.ai_summarizer.summarize(item.title)
            result["summary"] = summary
        
        return result
    
    async def analyze_items(self, items: List[TrendItemCreate]) -> List[Dict[str, Any]]:
        """批量分析热点条目"""
        results = []
        for item in items:
            analysis = await self.analyze_item(item)
            results.append(analysis)
        return results
    
    def calculate_hot_score(self, rank: int, base_score: float = 0) -> float:
        """
        计算热度分数
        排名越靠前，分数越高
        """
        if rank <= 0:
            rank = 50
        
        # 基于排名的基础分数 (100 - rank*2)
        rank_score = max(0, 100 - rank * 2)
        
        # 如果有基础热度值，进行加权
        if base_score > 0:
            # 将基础热度值归一化到 0-100
            normalized_base = min(100, base_score / 10000)
            return round((rank_score * 0.6 + normalized_base * 0.4), 2)
        
        return round(rank_score, 2)
    
    def detect_duplicates(self, items: List[TrendItemDB], threshold: float = 0.8) -> List[List[int]]:
        """
        检测重复/相似的热点
        使用简单的文本相似度算法
        返回相似文章的ID分组
        """
        from difflib import SequenceMatcher
        
        def similarity(a: str, b: str) -> float:
            return SequenceMatcher(None, a, b).ratio()
        
        n = len(items)
        visited = [False] * n
        groups = []
        
        for i in range(n):
            if visited[i]:
                continue
            
            group = [items[i].id]
            visited[i] = True
            
            for j in range(i + 1, n):
                if visited[j]:
                    continue
                
                sim = similarity(items[i].title, items[j].title)
                if sim >= threshold:
                    group.append(items[j].id)
                    visited[j] = True
            
            if len(group) > 1:
                groups.append(group)
        
        return groups


class TrendStatsCalculator:
    """热点统计计算器"""
    
    @staticmethod
    def calculate_platform_distribution(items: List[TrendItemDB]) -> Dict[str, int]:
        """计算平台分布"""
        distribution = {}
        for item in items:
            platform = item.platform
            distribution[platform] = distribution.get(platform, 0) + 1
        return distribution
    
    @staticmethod
    def calculate_sentiment_distribution(items: List[TrendItemDB]) -> Dict[str, int]:
        """计算情感分布"""
        distribution = {"positive": 0, "negative": 0, "neutral": 0}
        for item in items:
            sentiment = item.sentiment or "neutral"
            distribution[sentiment] = distribution.get(sentiment, 0) + 1
        return distribution
    
    @staticmethod
    def calculate_top_keywords(items: List[TrendItemDB], top_k: int = 10) -> List[Dict[str, Any]]:
        """计算热门关键词"""
        keyword_counts = {}
        
        for item in items:
            if item.keywords:
                for kw in item.keywords.split(","):
                    kw = kw.strip()
                    if kw:
                        keyword_counts[kw] = keyword_counts.get(kw, 0) + 1
        
        # 排序并返回前K个
        sorted_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)
        return [{"keyword": k, "count": v} for k, v in sorted_keywords[:top_k]]
    
    @staticmethod
    def calculate_hourly_trend(items: List[TrendItemDB]) -> List[Dict[str, Any]]:
        """计算小时趋势"""
        from collections import defaultdict
        
        hourly_data = defaultdict(int)
        
        for item in items:
            if item.created_at:
                hour_key = item.created_at.strftime("%H:00")
                hourly_data[hour_key] += 1
        
        # 按时间排序
        sorted_hours = sorted(hourly_data.items())
        return [{"hour": k, "count": v} for k, v in sorted_hours]
