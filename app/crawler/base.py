"""
爬虫基类
"""
import asyncio
import random
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

import httpx
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_config
from app.models import TrendItemCreate


@dataclass
class CrawlResult:
    """爬取结果"""
    success: bool
    items: List[TrendItemCreate]
    message: str = ""
    error: Optional[str] = None


class BaseCrawler(ABC):
    """爬虫基类"""
    
    def __init__(self):
        self.config = get_config()
        self.platform = self.get_platform_name()
        self.platform_config = self.config.platforms.get(self.platform)
        self.crawler_config = self.config.crawler
        
        self.headers = {
            "User-Agent": self.crawler_config.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        }
    
    @abstractmethod
    def get_platform_name(self) -> str:
        """获取平台名称"""
        pass
    
    @abstractmethod
    async def crawl(self) -> CrawlResult:
        """执行爬取"""
        pass
    
    @property
    def is_enabled(self) -> bool:
        """检查是否启用"""
        if not self.platform_config:
            return False
        return self.platform_config.enabled
    
    async def fetch(self, url: str, **kwargs) -> httpx.Response:
        """
        发送HTTP请求
        
        Args:
            url: 请求URL
            **kwargs: 额外请求参数
            
        Returns:
            HTTP响应
        """
        headers = {**self.headers, **kwargs.pop("headers", {})}
        
        async with httpx.AsyncClient(
            timeout=self.crawler_config.timeout,
            follow_redirects=True,
        ) as client:
            response = await client.get(url, headers=headers, **kwargs)
            response.raise_for_status()
            return response
    
    def parse_html(self, html: str) -> BeautifulSoup:
        """解析HTML"""
        return BeautifulSoup(html, "lxml")
    
    async def delay(self):
        """请求间隔延迟"""
        delay_time = self.crawler_config.delay + random.uniform(0, 1)
        await asyncio.sleep(delay_time)
    
    def create_item(
        self,
        title: str,
        url: Optional[str] = None,
        hot_score: int = 0,
        category: Optional[str] = None,
        author: Optional[str] = None,
        summary: Optional[str] = None,
        raw_data: Optional[Dict[str, Any]] = None,
    ) -> TrendItemCreate:
        """
        创建热点数据项
        
        Args:
            title: 标题
            url: URL
            hot_score: 热度分数
            category: 分类
            author: 作者
            summary: 摘要
            raw_data: 原始数据
            
        Returns:
            热点数据创建模型
        """
        return TrendItemCreate(
            title=title,
            url=url,
            platform=self.platform,
            hot_score=hot_score,
            category=category,
            author=author,
            summary=summary,
            raw_data=raw_data,
        )
    
    def extract_number(self, text: str) -> int:
        """
        从文本中提取数字
        
        Args:
            text: 包含数字的文本
            
        Returns:
            提取的数字
        """
        import re
        numbers = re.findall(r"\d+", text.replace(",", "").replace("万", "0000"))
        if numbers:
            return int(numbers[0])
        return 0
    
    def normalize_url(self, url: str, base_url: Optional[str] = None) -> str:
        """
        规范化URL
        
        Args:
            url: URL
            base_url: 基础URL
            
        Returns:
            规范化后的URL
        """
        if url.startswith("http"):
            return url
        if url.startswith("//"):
            return f"https:{url}"
        if url.startswith("/"):
            if base_url:
                from urllib.parse import urljoin
                return urljoin(base_url, url)
        return url
