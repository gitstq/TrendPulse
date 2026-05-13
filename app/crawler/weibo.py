"""
微博热搜爬虫
"""
import re
from typing import List
from urllib.parse import urljoin

from app.crawler.base import BaseCrawler, CrawlResult
from app.models import TrendItemCreate


class WeiboCrawler(BaseCrawler):
    """微博热搜爬虫"""
    
    def get_platform_name(self) -> str:
        return "weibo"
    
    async def crawl(self) -> CrawlResult:
        """爬取微博热搜"""
        if not self.is_enabled:
            return CrawlResult(success=False, items=[], message="微博爬虫未启用")
        
        try:
            url = self.platform_config.url or "https://s.weibo.com/top/summary"
            response = await self.fetch(url)
            html = response.text
            
            items = self._parse_hot_list(html)
            
            # 限制数量
            limit = self.platform_config.limit or 50
            items = items[:limit]
            
            return CrawlResult(
                success=True,
                items=items,
                message=f"成功爬取 {len(items)} 条微博热搜",
            )
            
        except Exception as e:
            return CrawlResult(
                success=False,
                items=[],
                error=str(e),
                message=f"微博热搜爬取失败: {str(e)}",
            )
    
    def _parse_hot_list(self, html: str) -> List[TrendItemCreate]:
        """解析微博热搜HTML"""
        items = []
        soup = self.parse_html(html)
        
        # 微博热搜列表
        hot_table = soup.select_one("#pl_top_realtimehot table")
        if not hot_table:
            return items
        
        rows = hot_table.select("tbody tr")
        
        for idx, row in enumerate(rows, 1):
            try:
                # 跳过表头
                if row.get("class") and "thead_tr" in row.get("class"):
                    continue
                
                # 提取排名
                rank_elem = row.select_one(".ranktop")
                rank = int(rank_elem.get_text(strip=True)) if rank_elem else idx
                
                # 提取标题和链接
                title_elem = row.select_one("td a")
                if not title_elem:
                    continue
                
                title = title_elem.get_text(strip=True)
                href = title_elem.get("href", "")
                url = urljoin("https://s.weibo.com", href) if href else ""
                
                # 提取热度
                hot_elem = row.select_one("td span")
                hot_score = 0
                if hot_elem:
                    hot_text = hot_elem.get_text(strip=True)
                    hot_score = self._extract_hot_score(hot_text)
                
                # 提取标签（爆、热、新等）
                tag_elem = row.select_one("td i")
                category = tag_elem.get_text(strip=True) if tag_elem else None
                
                if title:
                    trend_item = self.create_item(
                        title=title,
                        url=url,
                        hot_score=hot_score or (1000 - rank * 10),
                        category=category,
                    )
                    items.append(trend_item)
                    
            except Exception:
                continue
        
        return items
    
    def _extract_hot_score(self, text: str) -> int:
        """从文本中提取热度数值"""
        if not text:
            return 0
        
        # 微博热度格式：数字或带"万"
        match = re.search(r"(\d+(?:\.\d+)?)", text.replace(",", ""))
        if match:
            num = float(match.group(1))
            if "万" in text:
                return int(num * 10000)
            return int(num)
        
        return 0
