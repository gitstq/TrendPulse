"""
数据库操作模块
提供数据持久化和查询功能
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from contextlib import contextmanager

from sqlalchemy import create_engine, func, and_, or_
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError
from loguru import logger

from src.models import TrendItemDB, TrendItemCreate, TrendItem, Base
from src.config import DatabaseConfig


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.engine = self._create_engine()
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self._init_tables()
    
    def _create_engine(self):
        """创建数据库引擎"""
        if self.config.type == "sqlite":
            db_path = self.config.sqlite_path
            # 确保目录存在
            import os
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            db_url = f"sqlite:///{db_path}"
            return create_engine(
                db_url,
                connect_args={"check_same_thread": False},
                pool_size=self.config.pool_size,
                max_overflow=self.config.max_overflow
            )
        else:
            raise NotImplementedError(f"不支持的数据库类型: {self.config.type}")
    
    def _init_tables(self):
        """初始化数据库表"""
        Base.metadata.create_all(bind=self.engine)
        logger.info("数据库表初始化完成")
    
    @contextmanager
    def get_session(self) -> Session:
        """获取数据库会话上下文管理器"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def save_trend_items(self, items: List[TrendItemCreate], analyses: List[Dict[str, Any]]) -> int:
        """
        保存热点数据
        返回保存的数量
        """
        saved_count = 0
        
        with self.get_session() as session:
            for item, analysis in zip(items, analyses):
                try:
                    # 检查是否已存在相同标题的数据（今天内）
                    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
                    existing = session.query(TrendItemDB).filter(
                        and_(
                            TrendItemDB.title == item.title,
                            TrendItemDB.platform == item.platform,
                            TrendItemDB.created_at >= today
                        )
                    ).first()
                    
                    if existing:
                        # 更新现有记录
                        existing.hot_score = max(existing.hot_score, item.hot_score or 0)
                        existing.rank = item.rank or existing.rank
                        existing.mention_count += 1
                        existing.updated_at = datetime.utcnow()
                    else:
                        # 创建新记录
                        db_item = TrendItemDB(
                            title=item.title,
                            url=item.url,
                            platform=item.platform,
                            rank=item.rank,
                            hot_score=item.hot_score or 0,
                            sentiment=analysis.get("sentiment", "neutral"),
                            sentiment_score=analysis.get("sentiment_score", 0),
                            summary=analysis.get("summary"),
                            keywords=analysis.get("keywords"),
                            created_at=datetime.utcnow(),
                            updated_at=datetime.utcnow()
                        )
                        session.add(db_item)
                        saved_count += 1
                        
                except Exception as e:
                    logger.warning(f"保存热点数据失败: {e}")
                    continue
        
        logger.info(f"成功保存 {saved_count} 条热点数据")
        return saved_count
    
    def get_trend_items(
        self,
        platform: Optional[str] = None,
        sentiment: Optional[str] = None,
        keyword: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[TrendItemDB]:
        """查询热点数据"""
        with self.get_session() as session:
            query = session.query(TrendItemDB)
            
            if platform:
                query = query.filter(TrendItemDB.platform == platform)
            
            if sentiment:
                query = query.filter(TrendItemDB.sentiment == sentiment)
            
            if keyword:
                query = query.filter(
                    or_(
                        TrendItemDB.title.contains(keyword),
                        TrendItemDB.keywords.contains(keyword)
                    )
                )
            
            if start_time:
                query = query.filter(TrendItemDB.created_at >= start_time)
            
            if end_time:
                query = query.filter(TrendItemDB.created_at <= end_time)
            
            # 按热度排序
            query = query.order_by(TrendItemDB.hot_score.desc())
            
            return query.offset(offset).limit(limit).all()
    
    def get_trend_by_id(self, item_id: int) -> Optional[TrendItemDB]:
        """根据ID获取热点详情"""
        with self.get_session() as session:
            item = session.query(TrendItemDB).filter(TrendItemDB.id == item_id).first()
            if item:
                item.view_count += 1
            return item
    
    def get_latest_items(self, limit: int = 20) -> List[TrendItemDB]:
        """获取最新热点"""
        with self.get_session() as session:
            return session.query(TrendItemDB)\
                .order_by(TrendItemDB.created_at.desc())\
                .limit(limit)\
                .all()
    
    def get_hot_items(self, limit: int = 20) -> List[TrendItemDB]:
        """获取最热热点"""
        with self.get_session() as session:
            return session.query(TrendItemDB)\
                .order_by(TrendItemDB.hot_score.desc())\
                .limit(limit)\
                .all()
    
    def get_platform_stats(self) -> Dict[str, int]:
        """获取平台统计"""
        with self.get_session() as session:
            results = session.query(
                TrendItemDB.platform,
                func.count(TrendItemDB.id).label("count")
            ).group_by(TrendItemDB.platform).all()
            
            return {platform: count for platform, count in results}
    
    def get_sentiment_stats(self, days: int = 7) -> Dict[str, int]:
        """获取情感统计"""
        with self.get_session() as session:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            results = session.query(
                TrendItemDB.sentiment,
                func.count(TrendItemDB.id).label("count")
            ).filter(
                TrendItemDB.created_at >= start_date
            ).group_by(TrendItemDB.sentiment).all()
            
            return {sentiment: count for sentiment, count in results}
    
    def get_trend_stats(self, days: int = 7) -> Dict[str, Any]:
        """获取综合统计信息"""
        with self.get_session() as session:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # 总数量
            total_count = session.query(TrendItemDB).filter(
                TrendItemDB.created_at >= start_date
            ).count()
            
            # 今日数量
            today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            today_count = session.query(TrendItemDB).filter(
                TrendItemDB.created_at >= today
            ).count()
            
            # 平台分布
            platform_stats = self.get_platform_stats()
            
            # 情感分布
            sentiment_stats = self.get_sentiment_stats(days)
            
            return {
                "total_count": total_count,
                "today_count": today_count,
                "platform_stats": platform_stats,
                "sentiment_stats": sentiment_stats
            }
    
    def get_hourly_trend(self, days: int = 1) -> List[Dict[str, Any]]:
        """获取小时级趋势"""
        with self.get_session() as session:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            results = session.query(
                func.strftime('%H', TrendItemDB.created_at).label('hour'),
                func.count(TrendItemDB.id).label('count')
            ).filter(
                TrendItemDB.created_at >= start_date
            ).group_by('hour').order_by('hour').all()
            
            return [{"hour": h, "count": c} for h, c in results]
    
    def get_top_keywords(self, limit: int = 20, days: int = 7) -> List[Dict[str, Any]]:
        """获取热门关键词"""
        with self.get_session() as session:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            items = session.query(TrendItemDB).filter(
                TrendItemDB.created_at >= start_date
            ).all()
            
            keyword_counts = {}
            for item in items:
                if item.keywords:
                    for kw in item.keywords.split(","):
                        kw = kw.strip()
                        if kw:
                            keyword_counts[kw] = keyword_counts.get(kw, 0) + 1
            
            sorted_keywords = sorted(
                keyword_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )
            
            return [{"keyword": k, "count": v} for k, v in sorted_keywords[:limit]]
    
    def clean_old_data(self, retention_days: int = 30) -> int:
        """清理过期数据"""
        with self.get_session() as session:
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            
            deleted = session.query(TrendItemDB).filter(
                TrendItemDB.created_at < cutoff_date
            ).delete()
            
            logger.info(f"清理了 {deleted} 条过期数据")
            return deleted
    
    def get_item_history(self, title: str, days: int = 7) -> List[TrendItemDB]:
        """获取特定标题的历史记录"""
        with self.get_session() as session:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            return session.query(TrendItemDB).filter(
                and_(
                    TrendItemDB.title == title,
                    TrendItemDB.created_at >= start_date
                )
            ).order_by(TrendItemDB.created_at).all()
