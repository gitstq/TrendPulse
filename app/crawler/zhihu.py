"""
知乎热点爬虫
"""
import json
import re
from typing import List

from app.crawler.base import BaseCrawler, CrawlResult
from app.models import TrendItemCreate


class ZhihuCrawler(BaseCrawler):
    """知乎热榜爬虫"""
    
    def get_platform_name(self) -> str:
        return "zhihu"
    
    async def crawl(self) -> CrawlResult:
        """爬取知乎热榜"""
        if not self.is_enabled:
            return CrawlResult(success=False, items=[], message="知乎爬虫未启用")
        
        try:
            url = self.platform_config.url or "https://www.zhihu.com/hot"
            response = await self.fetch(url)
            html = response.text
            
            items = self._parse_hot_list(html)
            
            # 限制数量
            limit = self.platform_config.limit or 50
            items = items[:limit]
            
            return CrawlResult(
                success=True,
                items=items,
                message=f"成功爬取 {len(items)} 条知乎热榜",
            )
            
        except Exception as e:
            return CrawlResult(
                success=False,
                items=[],
                error=str(e),
                message=f"知乎热榜爬取失败: {str(e)}",
            )
    
    def _parse_hot_list(self, html: str) -> List[TrendItemCreate]:
        """解析知乎热榜HTML"""
        items = []
        soup = self.parse_html(html)
        
        # 知乎热榜通常在 script 标签中的 JSON 数据
        # 尝试从页面中提取初始数据
        scripts = soup.find_all("script", id="js-initialData")
        if scripts:
            try:
                data = json.loads(scripts[0].string)
                hot_list = data.get("initialState", {}).get("topstory", {}).get("hotList", [])
                
                for idx, item in enumerate(hot_list, 1):
                    try:
                        target = item.get("target", {})
                        title = target.get("titleArea", {}).get("text", "")
                        url = target.get("link", {}).get("url", "")
                        
                        # 提取热度
                        metrics = target.get("metricsArea", {}).get("text", "")
                        hot_score = self._extract_hot_score(metrics)
                        
                        # 提取摘要
                        excerpt = target.get("excerptArea", {}).get("text", "")
                        
                        if title:
                            trend_item = self.create_item(
                                title=title,
                                url=url,
                                hot_score=hot_score or (1000 - idx * 10),
                                summary=excerpt,
                                raw_data=item,
                            )
                            items.append(trend_item)
                    except Exception:
                        continue
                        
            except (json.JSONDecodeError, KeyError):
                pass
        
        # 如果上面的方法失败，尝试从HTML直接解析
        if not items:
            items = self._parse_html_directly(soup)
        
        return items
    
    def _parse_html_directly(self, soup) -> List[TrendItemCreate]:
        """直接从HTML解析热榜"""
        items = []
        
        # 查找热榜列表项
        hot_items = soup.select("[data-za-detail-view-path-module='HotList'] .HotItem")
        
        for idx, item in enumerate(hot_items, 1):
            try:
                # 提取标题
                title_elem = item.select_one(".HotItem-title")
                if not title_elem:
                    continue
                title = title_elem.get_text(strip=True)
                
                # 提取链接
                link_elem = item.select_one("a[href]")
                url = ""
                if link_elem:
                    href = link_elem.get("href", "")
                    url = self.normalize_url(href, "https://www.zhihu.com")
                
                # 提取热度
                metrics_elem = item.select_one(".HotItem-metrics")
                hot_score = 0
                if metrics_elem:
                    metrics_text = metrics_elem.get_text(strip=True)
                    hot_score = self._extract_hot_score(metrics_text)
                
                # 提取摘要
                excerpt_elem = item.select_one(".HotItem-excerpt")
                excerpt = excerpt_elem.get_text(strip=True) if excerpt_elem else ""
                
                if title:
                    trend_item = self.create_item(
                        title=title,
                        url=url,
                        hot_score=hot_score or (1000 - idx * 10),
                        summary=excerpt,
                    )
                    items.append(trend_item)
                    
            except Exception:
                continue
        
        return items
    
    def _extract_hot_score(self, text: str) -> int:
        """从文本中提取热度数值"""
        if not text:
            return 0
        
        # 匹配 "1234 万热度" 或 "1234热度" 格式
        match = re.search(r"(\d+(?:\.\d+)?)\s*万?\s*热度", text)
        if match:
            num = float(match.group(1))
            if "万" in text:
                return int(num * 10000)
            return int(num)
        
        # 直接提取数字
        numbers = re.findall(r"\d+", text.replace(",", ""))
        if numbers:
            return int(numbers[0])
        
        return 0
