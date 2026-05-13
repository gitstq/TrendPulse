"""
HackerNews爬虫
"""
from typing import List

from app.crawler.base import BaseCrawler, CrawlResult
from app.models import TrendItemCreate


class HackerNewsCrawler(BaseCrawler):
    """HackerNews爬虫"""
    
    def get_platform_name(self) -> str:
        return "hackernews"
    
    async def crawl(self) -> CrawlResult:
        """爬取HackerNews热门"""
        if not self.is_enabled:
            return CrawlResult(success=False, items=[], message="HackerNews爬虫未启用")
        
        try:
            # 使用官方API
            url = "https://hacker-news.firebaseio.com/v0/topstories.json"
            response = await self.fetch(url)
            story_ids = response.json()
            
            # 限制数量
            limit = min(self.platform_config.limit or 30, len(story_ids))
            story_ids = story_ids[:limit]
            
            items = []
            for story_id in story_ids:
                try:
                    story = await self._fetch_story(story_id)
                    if story:
                        items.append(story)
                except Exception:
                    continue
            
            return CrawlResult(
                success=True,
                items=items,
                message=f"成功爬取 {len(items)} 条HackerNews热门",
            )
            
        except Exception as e:
            return CrawlResult(
                success=False,
                items=[],
                error=str(e),
                message=f"HackerNews爬取失败: {str(e)}",
            )
    
    async def _fetch_story(self, story_id: int) -> TrendItemCreate:
        """获取单个故事详情"""
        url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
        response = await self.fetch(url)
        data = response.json()
        
        if not data:
            return None
        
        title = data.get("title", "")
        url_link = data.get("url", "")
        
        # 如果没有外部链接，使用HN讨论页
        if not url_link:
            url_link = f"https://news.ycombinator.com/item?id={story_id}"
        
        # 热度分数：基于分数和评论数
        score = data.get("score", 0)
        descendants = data.get("descendants", 0)
        hot_score = score + descendants * 2
        
        # 作者
        author = data.get("by", "")
        
        if title:
            return self.create_item(
                title=title,
                url=url_link,
                hot_score=hot_score,
                author=author,
                raw_data=data,
            )
        
        return None
