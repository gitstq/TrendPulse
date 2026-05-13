"""
GitHub Trending爬虫
"""
from typing import List
from urllib.parse import urljoin

from app.crawler.base import BaseCrawler, CrawlResult
from app.models import TrendItemCreate


class GithubCrawler(BaseCrawler):
    """GitHub Trending爬虫"""
    
    def get_platform_name(self) -> str:
        return "github"
    
    async def crawl(self) -> CrawlResult:
        """爬取GitHub Trending"""
        if not self.is_enabled:
            return CrawlResult(success=False, items=[], message="GitHub爬虫未启用")
        
        try:
            url = self.platform_config.url or "https://github.com/trending"
            response = await self.fetch(url)
            html = response.text
            
            items = self._parse_hot_list(html)
            
            # 限制数量
            limit = self.platform_config.limit or 25
            items = items[:limit]
            
            return CrawlResult(
                success=True,
                items=items,
                message=f"成功爬取 {len(items)} 条GitHub Trending",
            )
            
        except Exception as e:
            return CrawlResult(
                success=False,
                items=[],
                error=str(e),
                message=f"GitHub Trending爬取失败: {str(e)}",
            )
    
    def _parse_hot_list(self, html: str) -> List[TrendItemCreate]:
        """解析GitHub Trending HTML"""
        items = []
        soup = self.parse_html(html)
        
        # GitHub Trending列表项
        article_list = soup.select("article.Box-row")
        
        for idx, article in enumerate(article_list, 1):
            try:
                # 提取仓库名和链接
                link_elem = article.select_one("h2 a")
                if not link_elem:
                    continue
                
                repo_name = link_elem.get_text(strip=True).replace(" ", "").replace("\n", "")
                href = link_elem.get("href", "")
                url = urljoin("https://github.com", href)
                
                # 提取描述
                desc_elem = article.select_one("p.col-9")
                summary = desc_elem.get_text(strip=True) if desc_elem else ""
                
                # 提取编程语言
                lang_elem = article.select_one("[itemprop='programmingLanguage']")
                language = lang_elem.get_text(strip=True) if lang_elem else "Unknown"
                
                # 提取Stars数
                stars_elem = article.select("a.Link--muted")
                stars = 0
                forks = 0
                
                for star_elem in stars_elem:
                    text = star_elem.get_text(strip=True)
                    if "star" in text.lower():
                        stars = self._parse_number(text)
                    elif "fork" in text.lower():
                        forks = self._parse_number(text)
                
                # 提取今日新增Stars
                today_stars_elem = article.select_one("span.d-inline-block.float-sm-right")
                today_stars = 0
                if today_stars_elem:
                    today_text = today_stars_elem.get_text(strip=True)
                    today_stars = self._parse_number(today_text)
                
                # 热度分数：今日新增stars * 100 + 总stars
                hot_score = today_stars * 100 + min(stars // 100, 1000)
                
                if repo_name:
                    trend_item = self.create_item(
                        title=repo_name,
                        url=url,
                        hot_score=hot_score or (1000 - idx * 20),
                        category=language,
                        summary=summary,
                        raw_data={
                            "stars": stars,
                            "forks": forks,
                            "today_stars": today_stars,
                        },
                    )
                    items.append(trend_item)
                    
            except Exception:
                continue
        
        return items
    
    def _parse_number(self, text: str) -> int:
        """解析数字（支持k/m后缀）"""
        if not text:
            return 0
        
        text = text.strip().lower().replace(",", "")
        
        try:
            if "k" in text:
                return int(float(text.replace("k", "")) * 1000)
            elif "m" in text:
                return int(float(text.replace("m", "")) * 1000000)
            else:
                # 提取数字
                import re
                numbers = re.findall(r"\d+", text)
                if numbers:
                    return int(numbers[0])
        except (ValueError, IndexError):
            pass
        
        return 0
