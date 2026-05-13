"""
爬虫模块
"""
from app.crawler.base import BaseCrawler
from app.crawler.zhihu import ZhihuCrawler
from app.crawler.weibo import WeiboCrawler
from app.crawler.bilibili import BilibiliCrawler
from app.crawler.github import GithubCrawler
from app.crawler.hackernews import HackerNewsCrawler

__all__ = [
    "BaseCrawler",
    "ZhihuCrawler",
    "WeiboCrawler",
    "BilibiliCrawler",
    "GithubCrawler",
    "HackerNewsCrawler",
]
