"""
热点趋势分析器
"""
import json
import re
from typing import Optional

from app.analyzer.base import BaseAnalyzer
from app.analyzer.openai_client import OpenAIClient
from app.config import get_config
from app.models import TrendItem, AnalysisResult, SentimentType, PriorityType


class TrendAnalyzer(BaseAnalyzer):
    """热点趋势AI分析器"""
    
    def __init__(self):
        self.config = get_config()
        self.ai_config = self.config.ai
        self.analysis_config = self.config.analysis
        self.openai_client = OpenAIClient()
    
    async def analyze(self, item: TrendItem) -> Optional[AnalysisResult]:
        """
        分析热点数据
        
        Args:
            item: 热点数据
            
        Returns:
            分析结果
        """
        if not self.ai_config.api_key:
            return None
        
        if not self.analysis_config.enabled:
            return None
        
        if item.hot_score < self.analysis_config.min_hot_score:
            return None
        
        try:
            # 构建提示词
            prompt = self._build_prompt(item)
            
            # 系统提示词
            system_prompt = """你是一个专业的新闻热点分析助手。请对提供的热点话题进行深度分析。

请以JSON格式返回分析结果，格式如下：
{
    "sentiment": "positive/negative/neutral/mixed",
    "sentiment_score": 0.5,
    "keywords": ["关键词1", "关键词2", "关键词3"],
    "summary": "话题摘要",
    "trends": "发展趋势分析",
    "priority": "high/medium/low"
}

注意：
- sentiment_score范围是-1.0到1.0，-1.0表示极度负面，1.0表示极度正面
- keywords最多5个，按重要性排序
- summary不超过100字
- trends不超过150字
- priority根据话题重要性和紧急程度判断"""
            
            # 调用AI分析
            response = await self.openai_client.analyze_text(
                text=prompt,
                system_prompt=system_prompt,
                json_mode=True,
            )
            
            # 解析JSON响应
            result_data = json.loads(response)
            
            # 构建分析结果
            result = AnalysisResult(
                sentiment=SentimentType(result_data.get("sentiment", "neutral")),
                sentiment_score=float(result_data.get("sentiment_score", 0)),
                keywords=result_data.get("keywords", [])[:5],
                summary=result_data.get("summary", ""),
                trends=result_data.get("trends", ""),
                priority=PriorityType(result_data.get("priority", "medium")),
            )
            
            return result
            
        except Exception as e:
            # 分析失败，返回默认结果
            return self._get_default_result()
    
    def _build_prompt(self, item: TrendItem) -> str:
        """构建分析提示词"""
        template = self.analysis_config.prompt_template
        
        # 替换模板变量
        prompt = template.format(
            title=item.title,
            platform=item.platform,
            hot_score=item.hot_score,
        )
        
        # 添加额外信息
        if item.summary:
            prompt += f"\n\n摘要：{item.summary}"
        
        if item.author:
            prompt += f"\n作者：{item.author}"
        
        if item.category:
            prompt += f"\n分类：{item.category}"
        
        return prompt
    
    def _get_default_result(self) -> AnalysisResult:
        """获取默认分析结果"""
        return AnalysisResult(
            sentiment=SentimentType.NEUTRAL,
            sentiment_score=0.0,
            keywords=[],
            summary="暂无分析结果",
            trends="暂无趋势分析",
            priority=PriorityType.MEDIUM,
        )
    
    async def health_check(self) -> bool:
        """健康检查"""
        return await self.openai_client.health_check()
    
    def extract_keywords(self, text: str, max_keywords: int = 5) -> list:
        """
        简单关键词提取（备用方法）
        
        Args:
            text: 文本
            max_keywords: 最大关键词数
            
        Returns:
            关键词列表
        """
        # 简单的中文分词（基于常见停用词过滤）
        import jieba
        
        # 停用词
        stopwords = set([
            "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一", "一个", "上", "也",
            "很", "到", "说", "要", "去", "你", "会", "着", "没有", "看", "好", "自己", "这",
        ])
        
        # 分词
        words = jieba.lcut(text)
        
        # 过滤停用词和短词
        keywords = [
            word for word in words
            if len(word) > 1 and word not in stopwords
        ]
        
        # 统计词频
        from collections import Counter
        word_counts = Counter(keywords)
        
        # 返回最常见的关键词
        return [word for word, _ in word_counts.most_common(max_keywords)]
