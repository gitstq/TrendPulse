"""
热点爬虫模块
支持多平台热点数据抓取
"""

import asyncio
import json
import re
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional, Dict, Any
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup
from loguru import logger

from src.models import TrendItemCreate, CrawlResult


class BaseCrawler(ABC):
    """爬虫基类"""
    
    def __init__(self, platform: str, config: Dict[str, Any]):
        self.platform = platform
        self.config = config
        self.enabled = config.get("enabled", True)
        self.url = config.get("url", "")
        self.priority = config.get("priority", 1)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }
    
    @abstractmethod
    async def crawl(self) -> List[TrendItemCreate]:
        """执行爬取，返回热点列表"""
        pass
    
    async def fetch(self, url: str, **kwargs) -> Optional[str]:
        """获取页面内容"""
        try:
            async with httpx.AsyncClient(headers=self.headers, timeout=30) as client:
                response = await client.get(url, **kwargs)
                response.raise_for_status()
                return response.text
        except Exception as e:
            logger.error(f"[{self.platform}] 请求失败: {e}")
            return None
    
    async def fetch_json(self, url: str, **kwargs) -> Optional[Dict]:
        """获取JSON数据"""
        try:
            async with httpx.AsyncClient(headers=self.headers, timeout=30) as client:
                response = await client.get(url, **kwargs)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"[{self.platform}] JSON请求失败: {e}")
            return None


class WeiboCrawler(BaseCrawler):
    """微博热搜爬虫"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("weibo", config)
    
    async def crawl(self) -> List[TrendItemCreate]:
        """爬取微博热搜"""
        html = await self.fetch(self.url)
        if not html:
            return []
        
        items = []
        try:
            soup = BeautifulSoup(html, 'html.parser')
            # 微博热搜列表
            tbody = soup.find('tbody')
            if tbody:
                rows = tbody.find_all('tr')[1:]  # 跳过表头
                for idx, row in enumerate(rows[:50], 1):  # 前50条
                    try:
                        td_list = row.find_all('td')
                        if len(td_list) >= 2:
                            rank = idx
                            title_td = td_list[1]
                            a_tag = title_td.find('a')
                            if a_tag:
                                title = a_tag.get_text(strip=True)
                                url = urljoin("https://s.weibo.com", a_tag.get('href', ''))
                                
                                # 获取热度值
                                hot_span = title_td.find('span')
                                hot_score = 0
                                if hot_span:
                                    hot_text = hot_span.get_text(strip=True)
                                    hot_match = re.search(r'(\d+)', hot_text.replace(',', ''))
                                    if hot_match:
                                        hot_score = float(hot_match.group(1))
                                
                                items.append(TrendItemCreate(
                                    title=title,
                                    url=url,
                                    platform="weibo",
                                    rank=rank,
                                    hot_score=hot_score
                                ))
                    except Exception as e:
                        logger.warning(f"[weibo] 解析条目失败: {e}")
                        continue
        except Exception as e:
            logger.error(f"[weibo] 解析失败: {e}")
        
        logger.info(f"[weibo] 成功爬取 {len(items)} 条数据")
        return items


class ZhihuCrawler(BaseCrawler):
    """知乎热榜爬虫"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("zhihu", config)
        self.headers.update({
            "x-api-version": "3.0.76",
            "x-app-za": "OS=Web",
        })
    
    async def crawl(self) -> List[TrendItemCreate]:
        """爬取知乎热榜"""
        # 知乎使用API获取热榜数据
        api_url = "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total"
        
        data = await self.fetch_json(api_url)
        if not data or "data" not in data:
            return []
        
        items = []
        try:
            for idx, item in enumerate(data["data"][:50], 1):
                try:
                    title = item.get("target", {}).get("title", "")
                    url = item.get("target", {}).get("url", "")
                    if url and not url.startswith("http"):
                        url = f"https://www.zhihu.com{url}"
                    
                    # 热度值
                    hot_score = item.get("detail_text", "")
                    hot_match = re.search(r'(\d+)', hot_score.replace(",", ""))
                    score = float(hot_match.group(1)) if hot_match else 0
                    
                    if title:
                        items.append(TrendItemCreate(
                            title=title,
                            url=url,
                            platform="zhihu",
                            rank=idx,
                            hot_score=score
                        ))
                except Exception as e:
                    logger.warning(f"[zhihu] 解析条目失败: {e}")
                    continue
        except Exception as e:
            logger.error(f"[zhihu] 解析失败: {e}")
        
        logger.info(f"[zhihu] 成功爬取 {len(items)} 条数据")
        return items


class BaiduCrawler(BaseCrawler):
    """百度热搜爬虫"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("baidu", config)
    
    async def crawl(self) -> List[TrendItemCreate]:
        """爬取百度热搜"""
        html = await self.fetch(self.url)
        if not html:
            return []
        
        items = []
        try:
            # 百度热搜数据在页面script中
            match = re.search(r'<!--s-data:(.*?)-->', html, re.DOTALL)
            if match:
                data = json.loads(match.group(1))
                cards = data.get("cards", [])
                for card in cards:
                    content = card.get("content", [])
                    for idx, item in enumerate(content[:50], 1):
                        try:
                            title = item.get("word", "")
                            url = item.get("rawUrl", "")
                            hot_score = item.get("hotScore", 0)
                            
                            if title:
                                items.append(TrendItemCreate(
                                    title=title,
                                    url=url,
                                    platform="baidu",
                                    rank=idx,
                                    hot_score=float(hot_score)
                                ))
                        except Exception as e:
                            logger.warning(f"[baidu] 解析条目失败: {e}")
                            continue
        except Exception as e:
            logger.error(f"[baidu] 解析失败: {e}")
        
        logger.info(f"[baidu] 成功爬取 {len(items)} 条数据")
        return items


class BilibiliCrawler(BaseCrawler):
    """B站热搜爬虫"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("bilibili", config)
    
    async def crawl(self) -> List[TrendItemCreate]:
        """爬取B站热搜"""
        # B站热搜API
        api_url = "https://api.bilibili.com/x/web-interface/search/square"
        
        data = await self.fetch_json(api_url)
        if not data or data.get("code") != 0:
            return []
        
        items = []
        try:
            trending_list = data.get("data", {}).get("trending", {}).get("list", [])
            for idx, item in enumerate(trending_list[:50], 1):
                try:
                    title = item.get("keyword", "")
                    url = f"https://search.bilibili.com/all?keyword={title}"
                    hot_score = item.get("heat_score", 0)
                    
                    if title:
                        items.append(TrendItemCreate(
                            title=title,
                            url=url,
                            platform="bilibili",
                            rank=idx,
                            hot_score=float(hot_score)
                        ))
                except Exception as e:
                    logger.warning(f"[bilibili] 解析条目失败: {e}")
                    continue
        except Exception as e:
            logger.error(f"[bilibili] 解析失败: {e}")
        
        logger.info(f"[bilibili] 成功爬取 {len(items)} 条数据")
        return items


class ToutiaoCrawler(BaseCrawler):
    """今日头条热搜爬虫"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("toutiao", config)
    
    async def crawl(self) -> List[TrendItemCreate]:
        """爬取今日头条热搜"""
        html = await self.fetch(self.url)
        if not html:
            return []
        
        items = []
        try:
            # 今日头条数据在页面中
            match = re.search(r'window\._SSR_HYDRATED_DATA\s*=\s*(.*?)</script>', html, re.DOTALL)
            if match:
                data = json.loads(match.group(1).replace(":undefined", ":null"))
                hot_list = data.get("InitialState", {}).get("hotEvent", {}).get("data", [])
                
                for idx, item in enumerate(hot_list[:50], 1):
                    try:
                        title = item.get("Title", "")
                        url = item.get("Url", "")
                        hot_score = item.get("HotValue", 0)
                        
                        if title:
                            items.append(TrendItemCreate(
                                title=title,
                                url=url,
                                platform="toutiao",
                                rank=idx,
                                hot_score=float(hot_score)
                            ))
                    except Exception as e:
                        logger.warning(f"[toutiao] 解析条目失败: {e}")
                        continue
        except Exception as e:
            logger.error(f"[toutiao] 解析失败: {e}")
        
        logger.info(f"[toutiao] 成功爬取 {len(items)} 条数据")
        return items


class DouyinCrawler(BaseCrawler):
    """抖音热搜爬虫"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("douyin", config)
        self.headers.update({
            "Referer": "https://www.douyin.com/",
        })
    
    async def crawl(self) -> List[TrendItemCreate]:
        """爬取抖音热搜"""
        # 抖音热搜API
        api_url = "https://www.douyin.com/aweme/v1/web/hot/search/list/?device_platform=webapp"
        
        data = await self.fetch_json(api_url)
        if not data or data.get("status_code") != 0:
            return []
        
        items = []
        try:
            word_list = data.get("data", {}).get("word_list", [])
            for idx, item in enumerate(word_list[:50], 1):
                try:
                    title = item.get("word", "")
                    url = f"https://www.douyin.com/search/{title}"
                    hot_score = item.get("hot_value", 0)
                    
                    if title:
                        items.append(TrendItemCreate(
                            title=title,
                            url=url,
                            platform="douyin",
                            rank=idx,
                            hot_score=float(hot_score)
                        ))
                except Exception as e:
                    logger.warning(f"[douyin] 解析条目失败: {e}")
                    continue
        except Exception as e:
            logger.error(f"[douyin] 解析失败: {e}")
        
        logger.info(f"[douyin] 成功爬取 {len(items)} 条数据")
        return items


class CrawlerManager:
    """爬虫管理器"""
    
    def __init__(self, platforms_config: Dict[str, Any]):
        self.crawlers = []
        self._init_crawlers(platforms_config)
    
    def _init_crawlers(self, config: Dict[str, Any]):
        """初始化爬虫实例"""
        crawler_map = {
            "weibo": WeiboCrawler,
            "zhihu": ZhihuCrawler,
            "baidu": BaiduCrawler,
            "bilibili": BilibiliCrawler,
            "toutiao": ToutiaoCrawler,
            "douyin": DouyinCrawler,
        }
        
        for platform, crawler_class in crawler_map.items():
            platform_config = config.get(platform, {})
            if platform_config.get("enabled", True):
                self.crawlers.append(crawler_class(platform_config))
                logger.info(f"[CrawlerManager] 已加载 {platform} 爬虫")
    
    async def crawl_all(self) -> Dict[str, CrawlResult]:
        """执行所有爬虫"""
        results = {}
        
        tasks = []
        for crawler in self.crawlers:
            task = self._crawl_single(crawler)
            tasks.append(task)
        
        crawl_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for crawler, result in zip(self.crawlers, crawl_results):
            if isinstance(result, Exception):
                results[crawler.platform] = CrawlResult(
                    platform=crawler.platform,
                    success=False,
                    items_count=0,
                    message=str(result)
                )
            else:
                results[crawler.platform] = result
        
        return results
    
    async def _crawl_single(self, crawler: BaseCrawler) -> CrawlResult:
        """执行单个爬虫"""
        try:
            items = await crawler.crawl()
            return CrawlResult(
                platform=crawler.platform,
                success=True,
                items_count=len(items),
                message="成功",
                items=items
            )
        except Exception as e:
            logger.error(f"[{crawler.platform}] 爬取失败: {e}")
            return CrawlResult(
                platform=crawler.platform,
                success=False,
                items_count=0,
                message=str(e)
            )
