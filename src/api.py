"""
FastAPI Web API模块
提供RESTful API接口和Web界面
"""

from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from loguru import logger

from src.config import Settings, load_settings
from src.database import DatabaseManager
from src.models import (
    TrendItemResponse, TrendStats, PlatformStatus, 
    DashboardData, TrendItemCreate
)
from src.crawler import CrawlerManager
from src.analyzer import TrendAnalyzer, TrendStatsCalculator


# 创建FastAPI应用
app = FastAPI(
    title="TrendPulse API",
    description="智能热点监控分析平台API",
    version="1.0.0"
)

# 挂载静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")

# 模板引擎
templates = Jinja2Templates(directory="templates")

# 全局配置和数据库管理器
settings = load_settings()
db_manager = DatabaseManager(settings.database)


# ============== 依赖注入 ==============

def get_db():
    """获取数据库管理器"""
    return db_manager


def get_crawler_manager():
    """获取爬虫管理器"""
    return CrawlerManager(settings.platforms.model_dump())


def get_analyzer():
    """获取分析器"""
    return TrendAnalyzer(settings.ai)


# ============== API模型 ==============

class CrawlRequest(BaseModel):
    """爬虫请求"""
    platforms: Optional[List[str]] = None  # 指定平台，None表示全部


class CrawlResponse(BaseModel):
    """爬虫响应"""
    success: bool
    message: str
    total_items: int
    platform_results: dict


class FilterRequest(BaseModel):
    """筛选请求"""
    platform: Optional[str] = None
    sentiment: Optional[str] = None
    keyword: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = 50


# ============== Web页面路由 ==============

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """首页"""
    return templates.TemplateResponse("index.html", {
        "request": request,
        "app_name": settings.app.name,
        "version": settings.app.version
    })


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """仪表盘页面"""
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "app_name": settings.app.name
    })


@app.get("/trends", response_class=HTMLResponse)
async def trends_page(request: Request):
    """热点列表页面"""
    return templates.TemplateResponse("trends.html", {
        "request": request,
        "app_name": settings.app.name
    })


@app.get("/analytics", response_class=HTMLResponse)
async def analytics_page(request: Request):
    """分析页面"""
    return templates.TemplateResponse("analytics.html", {
        "request": request,
        "app_name": settings.app.name
    })


# ============== API路由 - 热点数据 ==============

@app.get("/api/trends", response_model=List[TrendItemResponse])
async def get_trends(
    platform: Optional[str] = Query(None, description="平台筛选"),
    sentiment: Optional[str] = Query(None, description="情感筛选"),
    keyword: Optional[str] = Query(None, description="关键词筛选"),
    days: int = Query(7, description="最近N天"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: DatabaseManager = Depends(get_db)
):
    """获取热点列表"""
    start_time = datetime.utcnow() - timedelta(days=days)
    
    items = db.get_trend_items(
        platform=platform,
        sentiment=sentiment,
        keyword=keyword,
        start_time=start_time,
        limit=limit,
        offset=offset
    )
    
    return [TrendItemResponse.model_validate(item) for item in items]


@app.get("/api/trends/{item_id}", response_model=TrendItemResponse)
async def get_trend_detail(
    item_id: int,
    db: DatabaseManager = Depends(get_db)
):
    """获取热点详情"""
    item = db.get_trend_by_id(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="热点不存在")
    return TrendItemResponse.model_validate(item)


@app.get("/api/trends/latest")
async def get_latest_trends(
    limit: int = Query(20, ge=1, le=100),
    db: DatabaseManager = Depends(get_db)
):
    """获取最新热点"""
    items = db.get_latest_items(limit=limit)
    return [TrendItemResponse.model_validate(item) for item in items]


@app.get("/api/trends/hot")
async def get_hot_trends(
    limit: int = Query(20, ge=1, le=100),
    db: DatabaseManager = Depends(get_db)
):
    """获取最热热点"""
    items = db.get_hot_items(limit=limit)
    return [TrendItemResponse.model_validate(item) for item in items]


# ============== API路由 - 统计信息 ==============

@app.get("/api/stats")
async def get_stats(
    days: int = Query(7, ge=1, le=30),
    db: DatabaseManager = Depends(get_db)
):
    """获取统计数据"""
    return db.get_trend_stats(days=days)


@app.get("/api/stats/platforms")
async def get_platform_stats(db: DatabaseManager = Depends(get_db)):
    """获取平台统计"""
    return db.get_platform_stats()


@app.get("/api/stats/sentiment")
async def get_sentiment_stats(
    days: int = Query(7, ge=1, le=30),
    db: DatabaseManager = Depends(get_db)
):
    """获取情感统计"""
    return db.get_sentiment_stats(days=days)


@app.get("/api/stats/keywords")
async def get_keyword_stats(
    limit: int = Query(20, ge=1, le=50),
    days: int = Query(7, ge=1, le=30),
    db: DatabaseManager = Depends(get_db)
):
    """获取关键词统计"""
    return db.get_top_keywords(limit=limit, days=days)


@app.get("/api/stats/hourly")
async def get_hourly_stats(
    days: int = Query(1, ge=1, le=7),
    db: DatabaseManager = Depends(get_db)
):
    """获取小时趋势"""
    return db.get_hourly_trend(days=days)


# ============== API路由 - 爬虫控制 ==============

@app.post("/api/crawl", response_model=CrawlResponse)
async def trigger_crawl(
    request: CrawlRequest = None,
    db: DatabaseManager = Depends(get_db)
):
    """手动触发爬虫"""
    try:
        crawler_manager = get_crawler_manager()
        analyzer = get_analyzer()
        
        # 执行爬虫
        results = await crawler_manager.crawl_all()
        
        total_saved = 0
        platform_results = {}
        
        for platform, result in results.items():
            if result.success and hasattr(result, 'items'):
                # 分析数据
                analyses = await analyzer.analyze_items(result.items)
                # 保存到数据库
                saved = db.save_trend_items(result.items, analyses)
                total_saved += saved
                platform_results[platform] = {
                    "crawled": result.items_count,
                    "saved": saved
                }
            else:
                platform_results[platform] = {
                    "crawled": 0,
                    "saved": 0,
                    "error": result.message
                }
        
        return CrawlResponse(
            success=True,
            message="爬虫执行完成",
            total_items=total_saved,
            platform_results=platform_results
        )
        
    except Exception as e:
        logger.error(f"爬虫执行失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============== API路由 - 仪表盘 ==============

@app.get("/api/dashboard")
async def get_dashboard_data(db: DatabaseManager = Depends(get_db)):
    """获取仪表盘数据"""
    try:
        stats = db.get_trend_stats(days=7)
        
        # 平台状态
        platforms = []
        for platform_name in ["weibo", "zhihu", "baidu", "bilibili", "toutiao", "douyin"]:
            platform_config = getattr(settings.platforms, platform_name, None)
            if platform_config:
                platforms.append(PlatformStatus(
                    platform=platform_name,
                    enabled=platform_config.enabled,
                    last_crawl=None,
                    item_count=stats["platform_stats"].get(platform_name, 0),
                    status="ok" if platform_config.enabled else "disabled"
                ))
        
        # 最新热点
        latest_items = db.get_latest_items(limit=10)
        
        # 图表数据
        sentiment_data = db.get_sentiment_stats(days=7)
        platform_data = stats["platform_stats"]
        hourly_data = db.get_hourly_trend(days=1)
        
        return DashboardData(
            total_items=stats["total_count"],
            today_items=stats["today_count"],
            active_platforms=sum(1 for p in platforms if p.enabled),
            platforms=platforms,
            latest_items=[TrendItemResponse.model_validate(item) for item in latest_items],
            sentiment_chart={
                "labels": list(sentiment_data.keys()),
                "data": list(sentiment_data.values())
            },
            platform_chart={
                "labels": list(platform_data.keys()),
                "data": list(platform_data.values())
            },
            trend_chart={
                "labels": [h["hour"] for h in hourly_data],
                "data": [h["count"] for h in hourly_data]
            }
        )
        
    except Exception as e:
        logger.error(f"获取仪表盘数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============== API路由 - 配置信息 ==============

@app.get("/api/config")
async def get_config():
    """获取公开配置信息"""
    return {
        "app": {
            "name": settings.app.name,
            "version": settings.app.version,
            "description": settings.app.description
        },
        "platforms": {
            name: {"enabled": config.enabled}
            for name, config in settings.platforms.model_dump().items()
        },
        "monitor": {
            "mode": settings.monitor.mode,
            "interval": settings.monitor.interval
        }
    }


# ============== 错误处理 ==============

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理"""
    logger.error(f"请求处理异常: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "服务器内部错误", "message": str(exc)}
    )


# ============== 启动事件 ==============

@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.info(f"🚀 {settings.app.name} v{settings.app.version} 启动成功")
    logger.info(f"📊 数据库: {settings.database.type}")
    logger.info(f"🤖 AI分析: {'已启用' if settings.ai.api_key else '未配置'}")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info(f"👋 {settings.app.name} 已关闭")
