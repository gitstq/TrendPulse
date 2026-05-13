"""
数据库操作模块
"""
import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager

from sqlalchemy import create_engine, select, update, delete, desc, func, and_
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.models import Base, TrendItemDB, TrendItem, TrendItemCreate, TrendItemUpdate
from app.config import get_config

# 数据库引擎
_engine = None
_async_engine = None
_SessionLocal = None
_AsyncSessionLocal = None


def init_database(database_url: Optional[str] = None):
    """初始化数据库"""
    global _engine, _async_engine, _SessionLocal, _AsyncSessionLocal
    
    config = get_config()
    
    if database_url is None:
        database_url = config.database.url
    
    # 确保数据目录存在
    if database_url.startswith("sqlite:///./"):
        db_path = database_url.replace("sqlite:///./", "")
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
    
    # 创建同步引擎
    connect_args = {"check_same_thread": False} if "sqlite" in database_url else {}
    _engine = create_engine(
        database_url,
        connect_args=connect_args,
        poolclass=StaticPool if "sqlite" in database_url else None,
        echo=config.app.debug,
    )
    
    # 创建异步引擎
    async_url = database_url
    if database_url.startswith("sqlite:///"):
        async_url = database_url.replace("sqlite:///", "sqlite+aiosqlite:///")
    
    _async_engine = create_async_engine(
        async_url,
        connect_args=connect_args,
        poolclass=StaticPool if "sqlite" in database_url else None,
        echo=config.app.debug,
    )
    
    # 创建会话工厂
    _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
    _AsyncSessionLocal = async_sessionmaker(
        autocommit=False, autoflush=False, bind=_async_engine, class_=AsyncSession
    )
    
    # 创建表
    Base.metadata.create_all(bind=_engine)
    
    return _engine


def get_db() -> Session:
    """获取数据库会话（同步）"""
    global _SessionLocal
    if _SessionLocal is None:
        init_database()
    
    db = _SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db() -> AsyncSession:
    """获取数据库会话（异步）"""
    global _AsyncSessionLocal
    if _AsyncSessionLocal is None:
        init_database()
    
    async with _AsyncSessionLocal() as session:
        yield session


@asynccontextmanager
async def async_db_session():
    """异步数据库会话上下文管理器"""
    global _AsyncSessionLocal
    if _AsyncSessionLocal is None:
        init_database()
    
    async with _AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


class TrendItemRepository:
    """热点数据仓库"""
    
    @staticmethod
    async def create(db: AsyncSession, item: TrendItemCreate) -> TrendItemDB:
        """创建热点数据"""
        db_item = TrendItemDB(
            title=item.title,
            url=item.url,
            platform=item.platform,
            hot_score=item.hot_score,
            category=item.category,
            author=item.author,
            summary=item.summary,
            content=item.content,
            raw_data=item.raw_data,
        )
        db.add(db_item)
        await db.commit()
        await db.refresh(db_item)
        return db_item
    
    @staticmethod
    async def get_by_id(db: AsyncSession, item_id: int) -> Optional[TrendItemDB]:
        """根据ID获取热点数据"""
        result = await db.execute(select(TrendItemDB).where(TrendItemDB.id == item_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_url(db: AsyncSession, url: str) -> Optional[TrendItemDB]:
        """根据URL获取热点数据"""
        result = await db.execute(select(TrendItemDB).where(TrendItemDB.url == url))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_title_and_platform(
        db: AsyncSession, title: str, platform: str
    ) -> Optional[TrendItemDB]:
        """根据标题和平台获取热点数据"""
        result = await db.execute(
            select(TrendItemDB).where(
                and_(
                    TrendItemDB.title == title,
                    TrendItemDB.platform == platform,
                )
            )
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def update(
        db: AsyncSession, item_id: int, item_update: TrendItemUpdate
    ) -> Optional[TrendItemDB]:
        """更新热点数据"""
        db_item = await TrendItemRepository.get_by_id(db, item_id)
        if not db_item:
            return None
        
        update_data = item_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_item, field, value)
        
        await db.commit()
        await db.refresh(db_item)
        return db_item
    
    @staticmethod
    async def delete(db: AsyncSession, item_id: int) -> bool:
        """删除热点数据"""
        result = await db.execute(
            delete(TrendItemDB).where(TrendItemDB.id == item_id)
        )
        await db.commit()
        return result.rowcount > 0
    
    @staticmethod
    async def list_items(
        db: AsyncSession,
        platform: Optional[str] = None,
        sentiment: Optional[str] = None,
        priority: Optional[str] = None,
        notified: Optional[bool] = None,
        analyzed: Optional[bool] = None,
        search: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[TrendItemDB]:
        """列表查询热点数据"""
        query = select(TrendItemDB)
        
        if platform:
            query = query.where(TrendItemDB.platform == platform)
        if sentiment:
            query = query.where(TrendItemDB.sentiment == sentiment)
        if priority:
            query = query.where(TrendItemDB.priority == priority)
        if notified is not None:
            query = query.where(TrendItemDB.notified == notified)
        if analyzed is not None:
            if analyzed:
                query = query.where(TrendItemDB.analyzed_at.isnot(None))
            else:
                query = query.where(TrendItemDB.analyzed_at.is_(None))
        if search:
            query = query.where(TrendItemDB.title.contains(search))
        if start_date:
            query = query.where(TrendItemDB.created_at >= start_date)
        if end_date:
            query = query.where(TrendItemDB.created_at <= end_date)
        
        query = query.order_by(desc(TrendItemDB.hot_score)).offset(skip).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def count_items(
        db: AsyncSession,
        platform: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> int:
        """统计热点数据数量"""
        query = select(func.count(TrendItemDB.id))
        
        if platform:
            query = query.where(TrendItemDB.platform == platform)
        if start_date:
            query = query.where(TrendItemDB.created_at >= start_date)
        if end_date:
            query = query.where(TrendItemDB.created_at <= end_date)
        
        result = await db.execute(query)
        return result.scalar()
    
    @staticmethod
    async def get_unanalyzed_items(
        db: AsyncSession, min_hot_score: int = 0, limit: int = 100
    ) -> List[TrendItemDB]:
        """获取未分析的热点数据"""
        query = (
            select(TrendItemDB)
            .where(
                and_(
                    TrendItemDB.analyzed_at.is_(None),
                    TrendItemDB.hot_score >= min_hot_score,
                )
            )
            .order_by(desc(TrendItemDB.hot_score))
            .limit(limit)
        )
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def get_unnotified_items(
        db: AsyncSession, limit: int = 100
    ) -> List[TrendItemDB]:
        """获取未通知的热点数据"""
        query = (
            select(TrendItemDB)
            .where(
                and_(
                    TrendItemDB.notified == False,
                    TrendItemDB.analyzed_at.isnot(None),
                )
            )
            .order_by(desc(TrendItemDB.hot_score))
            .limit(limit)
        )
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def get_platform_distribution(db: AsyncSession) -> Dict[str, int]:
        """获取平台分布统计"""
        query = (
            select(TrendItemDB.platform, func.count(TrendItemDB.id))
            .group_by(TrendItemDB.platform)
        )
        result = await db.execute(query)
        return {row[0]: row[1] for row in result.all()}
    
    @staticmethod
    async def get_sentiment_distribution(db: AsyncSession) -> Dict[str, int]:
        """获取情感分布统计"""
        query = (
            select(TrendItemDB.sentiment, func.count(TrendItemDB.id))
            .where(TrendItemDB.sentiment.isnot(None))
            .group_by(TrendItemDB.sentiment)
        )
        result = await db.execute(query)
        return {row[0]: row[1] for row in result.all()}
    
    @staticmethod
    async def get_recent_items(
        db: AsyncSession, hours: int = 24, limit: int = 10
    ) -> List[TrendItemDB]:
        """获取最近的热点数据"""
        since = datetime.utcnow() - timedelta(hours=hours)
        query = (
            select(TrendItemDB)
            .where(TrendItemDB.created_at >= since)
            .order_by(desc(TrendItemDB.created_at))
            .limit(limit)
        )
        result = await db.execute(query)
        return result.scalars().all()


class DashboardRepository:
    """仪表盘数据仓库"""
    
    @staticmethod
    async def get_stats(db: AsyncSession) -> Dict[str, Any]:
        """获取仪表盘统计数据"""
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        total_items = await TrendItemRepository.count_items(db)
        today_items = await TrendItemRepository.count_items(db, start_date=today)
        
        analyzed_query = select(func.count(TrendItemDB.id)).where(
            TrendItemDB.analyzed_at.isnot(None)
        )
        analyzed_result = await db.execute(analyzed_query)
        analyzed_items = analyzed_result.scalar()
        
        notified_query = select(func.count(TrendItemDB.id)).where(
            TrendItemDB.notified == True
        )
        notified_result = await db.execute(notified_query)
        notified_items = notified_result.scalar()
        
        platform_distribution = await TrendItemRepository.get_platform_distribution(db)
        sentiment_distribution = await TrendItemRepository.get_sentiment_distribution(db)
        recent_items = await TrendItemRepository.get_recent_items(db, limit=10)
        
        return {
            "total_items": total_items,
            "today_items": today_items,
            "analyzed_items": analyzed_items,
            "notified_items": notified_items,
            "platform_distribution": platform_distribution,
            "sentiment_distribution": sentiment_distribution,
            "recent_items": recent_items,
        }