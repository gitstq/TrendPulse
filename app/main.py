"""
TrendPulse - FastAPI主应用
"""
import os
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Request, Query, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import get_config
from app.database import init_database, async_db_session
from app.database import TrendItemRepository, DashboardRepository
from app.scheduler import TrendScheduler
from app.models import TrendItemCreate, TrendItemUpdate

# 初始化调度器
scheduler = TrendScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    config = get_config()
    
    # 初始化数据库
    init_database()
    print("✅ 数据库初始化完成")
    
    # 启动调度器
    scheduler.start()
    
    yield
    
    # 关闭时清理
    scheduler.stop()
    print("⏹️ 调度器已停止")


# 创建FastAPI应用
app = FastAPI(
    title="TrendPulse",
    description="多平台热点聚合AI分析工具",
    version="1.0.0",
    lifespan=lifespan,
)

# 挂载静态文件
app.mount("/static", StaticFiles(directory="app/web/static"), name="static")

# 模板引擎
templates = Jinja2Templates(directory="app/web/templates")


# ============ 页面路由 ============

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """仪表盘页面"""
    async with async_db_session() as db:
        stats = await DashboardRepository.get_stats(db)
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "stats": stats,
    })


@app.get("/trends", response_class=HTMLResponse)
async def trends_page(request: Request):
    """热点列表页面"""
    return templates.TemplateResponse("trends.html", {"request": request})


@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    """设置页面"""
    config = get_config()
    return templates.TemplateResponse("settings.html", {
        "request": request,
        "config": config,
    })


# ============ API路由 ============

@app.get("/api/trends")
async def get_trends(
    platform: Optional[str] = Query(None),
    sentiment: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    notified: Optional[bool] = Query(None),
    analyzed: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    """获取热点列表"""
    async with async_db_session() as db:
        skip = (page - 1) * limit
        
        items = await TrendItemRepository.list_items(
            db,
            platform=platform,
            sentiment=sentiment,
            priority=priority,
            notified=notified,
            analyzed=analyzed,
            search=search,
            skip=skip,
            limit=limit,
        )
        
        total = await TrendItemRepository.count_items(
            db,
            platform=platform,
        )
        
        from app.models import TrendItem
        
        return {
            "items": [TrendItem.model_validate(item).model_dump() for item in items],
            "total": total,
            "page": page,
            "limit": limit,
        }


@app.get("/api/trends/{item_id}")
async def get_trend(item_id: int):
    """获取单个热点详情"""
    async with async_db_session() as db:
        item = await TrendItemRepository.get_by_id(db, item_id)
        
        if not item:
            raise HTTPException(status_code=404, detail="热点数据不存在")
        
        from app.models import TrendItem
        return TrendItem.model_validate(item).model_dump()


@app.post("/api/crawl")
async def trigger_crawl():
    """手动触发爬虫"""
    try:
        import asyncio
        asyncio.create_task(scheduler.run_all_crawlers())
        
        return {
            "success": True,
            "message": "爬虫任务已启动",
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"启动失败: {str(e)}",
        }


@app.post("/api/analyze")
async def trigger_analyze():
    """手动触发AI分析"""
    try:
        import asyncio
        asyncio.create_task(scheduler._analyze_pending_items())
        
        return {
            "success": True,
            "message": "AI分析任务已启动",
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"启动失败: {str(e)}",
        }


@app.post("/api/notify")
async def trigger_notify():
    """手动触发通知"""
    try:
        import asyncio
        asyncio.create_task(scheduler._send_pending_notifications())
        
        return {
            "success": True,
            "message": "通知任务已启动",
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"启动失败: {str(e)}",
        }


@app.get("/api/stats")
async def get_stats():
    """获取统计数据"""
    async with async_db_session() as db:
        stats = await DashboardRepository.get_stats(db)
        
        # 转换recent_items
        from app.models import TrendItem
        stats["recent_items"] = [
            TrendItem.model_validate(item).model_dump()
            for item in stats["recent_items"]
        ]
        
        return stats


@app.get("/api/status")
async def get_status():
    """获取系统状态"""
    return scheduler.get_status()


@app.get("/api/config")
async def get_config_api():
    """获取配置（脱敏）"""
    config = get_config()
    
    return {
        "app": {
            "name": config.app.name,
            "version": config.app.version,
        },
        "platforms": {
            name: {"enabled": p.enabled}
            for name, p in config.platforms.items()
        },
        "notifiers": {
            name: {"enabled": n.enabled}
            for name, n in config.notifiers.items()
        },
        "scheduler": {
            "default_schedule": config.scheduler.default_schedule,
            "timezone": config.scheduler.timezone,
        },
        "analysis": {
            "enabled": config.analysis.enabled,
            "min_hot_score": config.analysis.min_hot_score,
        },
    }


# ============ 健康检查 ============

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
    }


@app.get("/api/health")
async def api_health_check():
    """API健康检查"""
    return await health_check()


# ============ 启动入口 ============

if __name__ == "__main__":
    import uvicorn
    
    config = get_config()
    
    uvicorn.run(
        "app.main:app",
        host=config.app.host,
        port=config.app.port,
        reload=config.app.debug,
    )
