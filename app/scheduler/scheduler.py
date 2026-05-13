"""
定时任务调度器
"""
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Callable

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import get_config
from app.database import async_db_session
from app.database import TrendItemRepository
from app.crawler import (
    ZhihuCrawler,
    WeiboCrawler,
    BilibiliCrawler,
    GithubCrawler,
    HackerNewsCrawler,
)
from app.analyzer import TrendAnalyzer
from app.notifier import (
    WechatNotifier,
    DingtalkNotifier,
    TelegramNotifier,
    EmailNotifier,
)


class TrendScheduler:
    """热点趋势定时任务调度器"""
    
    def __init__(self):
        self.config = get_config()
        self.scheduler_config = self.config.scheduler
        
        self.scheduler = AsyncIOScheduler(timezone=self.scheduler_config.timezone)
        
        # 爬虫实例
        self.crawlers = {
            "zhihu": ZhihuCrawler(),
            "weibo": WeiboCrawler(),
            "bilibili": BilibiliCrawler(),
            "github": GithubCrawler(),
            "hackernews": HackerNewsCrawler(),
        }
        
        # AI分析器
        self.analyzer = TrendAnalyzer()
        
        # 通知器
        self.notifiers = {
            "wechat": WechatNotifier(),
            "dingtalk": DingtalkNotifier(),
            "telegram": TelegramNotifier(),
            "email": EmailNotifier(),
        }
        
        self._running = False
        self._last_crawl_time: Optional[datetime] = None
    
    def start(self):
        """启动调度器"""
        if self._running:
            return
        
        # 添加爬虫任务
        self._add_crawl_jobs()
        
        # 添加AI分析任务
        self._add_analysis_job()
        
        # 添加通知任务
        self._add_notification_job()
        
        # 启动调度器
        self.scheduler.start()
        self._running = True
        
        print(f"✅ 调度器已启动，时区: {self.scheduler_config.timezone}")
        
        # 启动时立即执行一次
        if self.scheduler_config.run_on_startup:
            asyncio.create_task(self.run_all_crawlers())
    
    def stop(self):
        """停止调度器"""
        if not self._running:
            return
        
        self.scheduler.shutdown()
        self._running = False
        print("⏹️ 调度器已停止")
    
    def _add_crawl_jobs(self):
        """添加爬虫任务"""
        schedule = self.scheduler_config.default_schedule
        
        for platform, crawler in self.crawlers.items():
            job_id = f"crawl_{platform}"
            self.scheduler.add_job(
                self._crawl_platform,
                trigger=CronTrigger.from_crontab(schedule),
                id=job_id,
                name=f"爬取 {platform}",
                replace_existing=True,
                args=[platform],
            )
            print(f"📅 已添加爬虫任务: {platform} ({schedule})")
    
    def _add_analysis_job(self):
        """添加AI分析任务"""
        # 每5分钟执行一次分析
        self.scheduler.add_job(
            self._analyze_pending_items,
            trigger="interval",
            minutes=5,
            id="analyze_items",
            name="AI分析待处理热点",
            replace_existing=True,
        )
        print("📅 已添加AI分析任务 (每5分钟)")
    
    def _add_notification_job(self):
        """添加通知任务"""
        # 每2分钟执行一次通知
        self.scheduler.add_job(
            self._send_pending_notifications,
            trigger="interval",
            minutes=2,
            id="send_notifications",
            name="发送待处理通知",
            replace_existing=True,
        )
        print("📅 已添加通知任务 (每2分钟)")
    
    async def _crawl_platform(self, platform: str):
        """爬取指定平台"""
        crawler = self.crawlers.get(platform)
        if not crawler:
            return
        
        print(f"🕷️ 开始爬取 {platform}...")
        
        try:
            result = await crawler.crawl()
            
            if result.success:
                # 保存到数据库
                async with async_db_session() as db:
                    saved_count = 0
                    for item in result.items:
                        try:
                            # 检查是否已存在
                            existing = await TrendItemRepository.get_by_title_and_platform(
                                db, item.title, item.platform
                            )
                            if not existing:
                                await TrendItemRepository.create(db, item)
                                saved_count += 1
                        except Exception as e:
                            print(f"保存热点数据失败: {e}")
                    
                    print(f"✅ {platform} 爬取完成，新增 {saved_count} 条数据")
            else:
                print(f"❌ {platform} 爬取失败: {result.message}")
                
        except Exception as e:
            print(f"❌ {platform} 爬取异常: {e}")
        
        self._last_crawl_time = datetime.utcnow()
    
    async def _analyze_pending_items(self):
        """分析待处理的热点数据"""
        try:
            async with async_db_session() as db:
                # 获取未分析的热点
                items = await TrendItemRepository.get_unanalyzed_items(
                    db,
                    min_hot_score=self.config.analysis.min_hot_score,
                    limit=10,
                )
                
                if not items:
                    return
                
                print(f"🤖 开始分析 {len(items)} 条热点数据...")
                
                analyzed_count = 0
                for db_item in items:
                    try:
                        from app.models import TrendItem
                        item = TrendItem.model_validate(db_item)
                        
                        # AI分析
                        result = await self.analyzer.analyze(item)
                        
                        if result:
                            from app.models import TrendItemUpdate
                            update_data = TrendItemUpdate(
                                sentiment=result.sentiment,
                                sentiment_score=result.sentiment_score,
                                keywords=result.keywords,
                                analysis_result=f"{result.summary}\n\n发展趋势：{result.trends}",
                                priority=result.priority,
                                analyzed_at=datetime.utcnow(),
                            )
                            
                            await TrendItemRepository.update(
                                db, db_item.id, update_data
                            )
                            analyzed_count += 1
                            
                    except Exception as e:
                        print(f"分析热点数据失败: {e}")
                
                if analyzed_count > 0:
                    print(f"✅ 完成 {analyzed_count} 条热点数据的AI分析")
                    
        except Exception as e:
            print(f"AI分析任务异常: {e}")
    
    async def _send_pending_notifications(self):
        """发送待处理的通知"""
        try:
            async with async_db_session() as db:
                # 获取未通知的热点
                items = await TrendItemRepository.get_unnotified_items(db, limit=5)
                
                if not items:
                    return
                
                print(f"📢 开始发送 {len(items)} 条通知...")
                
                sent_count = 0
                for db_item in items:
                    try:
                        from app.models import TrendItem, TrendItemUpdate
                        item = TrendItem.model_validate(db_item)
                        
                        # 发送通知到所有启用的通知器
                        notification_sent = False
                        for notifier_type, notifier in self.notifiers.items():
                            if notifier.is_enabled():
                                try:
                                    success = await notifier.send(item)
                                    if success:
                                        notification_sent = True
                                except Exception as e:
                                    print(f"{notifier_type} 通知发送失败: {e}")
                        
                        # 标记为已通知
                        if notification_sent:
                            update_data = TrendItemUpdate(
                                notified=True,
                                notified_at=datetime.utcnow(),
                            )
                            await TrendItemRepository.update(
                                db, db_item.id, update_data
                            )
                            sent_count += 1
                            
                    except Exception as e:
                        print(f"发送通知失败: {e}")
                
                if sent_count > 0:
                    print(f"✅ 成功发送 {sent_count} 条通知")
                    
        except Exception as e:
            print(f"通知任务异常: {e}")
    
    async def run_all_crawlers(self):
        """手动执行所有爬虫"""
        print("🚀 手动执行所有爬虫...")
        
        tasks = []
        for platform in self.crawlers.keys():
            task = self._crawl_platform(platform)
            tasks.append(task)
        
        await asyncio.gather(*tasks, return_exceptions=True)
        
        print("✅ 所有爬虫执行完成")
    
    def get_status(self) -> Dict:
        """获取调度器状态"""
        return {
            "running": self._running,
            "last_crawl_time": self._last_crawl_time.isoformat() if self._last_crawl_time else None,
            "jobs": [
                {
                    "id": job.id,
                    "name": job.name,
                    "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                }
                for job in self.scheduler.get_jobs()
            ],
        }
