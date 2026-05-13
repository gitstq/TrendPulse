"""
B站热门爬虫
"""
import json
from typing import List

from app.crawler.base import BaseCrawler, CrawlResult
from app.models import TrendItemCreate


class BilibiliCrawler(BaseCrawler):
    """B站热门视频爬虫"""
    
    def get_platform_name(self) -> str:
        return "bilibili"
    
    async def crawl(self) -> CrawlResult:
        """爬取B站热门视频"""
        if not self.is_enabled:
            return CrawlResult(success=False, items=[], message="B站爬虫未启用")
        
        try:
            # B站API
            url = "https://api.bilibili.com/x/web-interface/ranking/v2"
            params = {
                "rid": 0,  # 全站
                "type": "all",
            }
            
            response = await self.fetch(url, params=params)
            data = response.json()
            
            items = self._parse_hot_list(data)
            
            # 限制数量
            limit = self.platform_config.limit or 50
            items = items[:limit]
            
            return CrawlResult(
                success=True,
                items=items,
                message=f"成功爬取 {len(items)} 条B站热门",
            )
            
        except Exception as e:
            return CrawlResult(
                success=False,
                items=[],
                error=str(e),
                message=f"B站热门爬取失败: {str(e)}",
            )
    
    def _parse_hot_list(self, data: dict) -> List[TrendItemCreate]:
        """解析B站热门数据"""
        items = []
        
        if data.get("code") != 0:
            return items
        
        list_data = data.get("data", {}).get("list", [])
        
        for idx, video in enumerate(list_data, 1):
            try:
                title = video.get("title", "")
                bvid = video.get("bvid", "")
                url = f"https://www.bilibili.com/video/{bvid}" if bvid else ""
                
                # 热度计算：综合播放、弹幕、评论
                stat = video.get("stat", {})
                view = stat.get("view", 0)
                danmaku = stat.get("danmaku", 0)
                reply = stat.get("reply", 0)
                
                # 热度分数
                hot_score = view + danmaku * 10 + reply * 50
                
                # 作者
                owner = video.get("owner", {})
                author = owner.get("name", "")
                
                # 摘要
                desc = video.get("desc", "")
                
                # 分类
                tname = video.get("tname", "")
                
                if title:
                    trend_item = self.create_item(
                        title=title,
                        url=url,
                        hot_score=hot_score,
                        category=tname,
                        author=author,
                        summary=desc[:200] if desc else None,
                        raw_data=video,
                    )
                    items.append(trend_item)
                    
            except Exception:
                continue
        
        return items
