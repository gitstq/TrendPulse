"""
AI分析器基类
"""
from abc import ABC, abstractmethod
from typing import Optional

from app.models import TrendItem, AnalysisResult


class BaseAnalyzer(ABC):
    """AI分析器基类"""
    
    def __init__(self):
        pass
    
    @abstractmethod
    async def analyze(self, item: TrendItem) -> Optional[AnalysisResult]:
        """
        分析热点数据
        
        Args:
            item: 热点数据
            
        Returns:
            分析结果
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """
        健康检查
        
        Returns:
            是否可用
        """
        pass
