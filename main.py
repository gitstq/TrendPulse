"""
TrendPulse - 智能热点监控分析平台
主入口文件

使用方法:
    python main.py              # 启动Web服务
    python main.py --crawl      # 执行一次爬虫
    python main.py --init-db    # 初始化数据库
"""

import argparse
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from loguru import logger
import uvicorn

from src.config import load_settings
from src.database import DatabaseManager
from src.crawler import CrawlerManager
from src.analyzer import TrendAnalyzer


def init_database():
    """初始化数据库"""
    logger.info("正在初始化数据库...")
    settings = load_settings()
    db = DatabaseManager(settings.database)
    logger.info("✅ 数据库初始化完成")


async def run_crawler():
    """执行爬虫任务"""
    logger.info("🕷️ 开始执行爬虫任务...")
    
    settings = load_settings()
    db = DatabaseManager(settings.database)
    crawler_manager = CrawlerManager(settings.platforms.model_dump())
    analyzer = TrendAnalyzer(settings.ai)
    
    # 执行爬虫
    results = await crawler_manager.crawl_all()
    
    total_saved = 0
    for platform, result in results.items():
        if result.success and hasattr(result, 'items'):
            logger.info(f"[{platform}] 爬取到 {len(result.items)} 条数据")
            # 分析数据
            analyses = await analyzer.analyze_items(result.items)
            # 保存到数据库
            saved = db.save_trend_items(result.items, analyses)
            total_saved += saved
            logger.info(f"[{platform}] 保存了 {saved} 条新数据")
        else:
            logger.warning(f"[{platform}] 爬取失败: {result.message}")
    
    logger.info(f"✅ 爬虫任务完成，共保存 {total_saved} 条数据")


def run_web_server():
    """启动Web服务"""
    settings = load_settings()
    
    logger.info(f"🚀 启动 {settings.app.name} v{settings.app.version}")
    logger.info(f"📡 服务地址: http://{settings.app.host}:{settings.app.port}")
    
    uvicorn.run(
        "src.api:app",
        host=settings.app.host,
        port=settings.app.port,
        reload=settings.app.debug,
        log_level="info"
    )


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="TrendPulse - 智能热点监控分析平台",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py              # 启动Web服务
  python main.py --crawl      # 执行一次爬虫
  python main.py --init-db    # 初始化数据库
  python main.py --crawl --web # 先执行爬虫，再启动Web服务
        """
    )
    
    parser.add_argument(
        "--crawl",
        action="store_true",
        help="执行爬虫任务"
    )
    
    parser.add_argument(
        "--init-db",
        action="store_true",
        help="初始化数据库"
    )
    
    parser.add_argument(
        "--web",
        action="store_true",
        help="启动Web服务"
    )
    
    parser.add_argument(
        "--config",
        type=str,
        default="config/config.yaml",
        help="配置文件路径 (默认: config/config.yaml)"
    )
    
    args = parser.parse_args()
    
    # 如果没有指定任何参数，默认启动Web服务
    if not (args.crawl or args.init_db or args.web):
        args.web = True
    
    # 初始化数据库
    if args.init_db:
        init_database()
        return
    
    # 执行爬虫
    if args.crawl:
        asyncio.run(run_crawler())
        if not args.web:
            return
    
    # 启动Web服务
    if args.web:
        run_web_server()


if __name__ == "__main__":
    main()
