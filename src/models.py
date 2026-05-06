"""
数据模型定义
包含数据库模型和API数据模型
"""

from datetime import datetime
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class SentimentType(str, Enum):
    """情感类型"""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class TrendItemDB(Base):
    """热点数据数据库模型"""
    __tablename__ = "trend_items"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False, index=True)
    url = Column(String(1000), nullable=True)
    platform = Column(String(50), nullable=False, index=True)
    rank = Column(Integer, nullable=True)
    hot_score = Column(Float, default=0.0)
    sentiment = Column(String(20), default=SentimentType.NEUTRAL.value)
    sentiment_score = Column(Float, default=0.0)
    summary = Column(Text, nullable=True)
    keywords = Column(String(500), nullable=True)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 统计字段
    view_count = Column(Integer, default=0)
    mention_count = Column(Integer, default=1)
    
    def __repr__(self):
        return f"<TrendItemDB(id={self.id}, title={self.title[:30]}..., platform={self.platform})>"


class TrendItem(BaseModel):
    """热点数据API模型"""
    id: Optional[int] = None
    title: str
    url: Optional[str] = None
    platform: str
    rank: Optional[int] = None
    hot_score: float = 0.0
    sentiment: SentimentType = SentimentType.NEUTRAL
    sentiment_score: float = 0.0
    summary: Optional[str] = None
    keywords: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    view_count: int = 0
    mention_count: int = 1
    
    class Config:
        from_attributes = True


class TrendItemCreate(BaseModel):
    """创建热点数据请求模型"""
    title: str = Field(..., min_length=1, max_length=500)
    url: Optional[str] = Field(None, max_length=1000)
    platform: str = Field(..., min_length=1, max_length=50)
    rank: Optional[int] = None
    hot_score: float = 0.0
    keywords: Optional[str] = None


class TrendItemResponse(BaseModel):
    """热点数据响应模型"""
    id: int
    title: str
    url: Optional[str]
    platform: str
    rank: Optional[int]
    hot_score: float
    sentiment: str
    sentiment_score: float
    summary: Optional[str]
    keywords: Optional[str]
    created_at: datetime
    mention_count: int


class TrendStats(BaseModel):
    """热点统计信息"""
    total_count: int
    platform_counts: dict
    sentiment_distribution: dict
    top_keywords: List[dict]
    hourly_trend: List[dict]


class PlatformStatus(BaseModel):
    """平台状态信息"""
    platform: str
    enabled: bool
    last_crawl: Optional[datetime]
    item_count: int
    status: str  # ok / error / disabled


class CrawlResult(BaseModel):
    """爬虫结果"""
    platform: str
    success: bool
    items_count: int
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class NotificationMessage(BaseModel):
    """通知消息"""
    title: str
    content: str
    items: List[TrendItem]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class DashboardData(BaseModel):
    """仪表盘数据"""
    total_items: int
    today_items: int
    active_platforms: int
    platforms: List[PlatformStatus]
    latest_items: List[TrendItemResponse]
    sentiment_chart: dict
    platform_chart: dict
    trend_chart: dict


# 数据库初始化函数
def init_database(db_url: str = "sqlite:///./data/trendpulse.db"):
    """初始化数据库"""
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal


def get_db_session(db_url: str = "sqlite:///./data/trendpulse.db"):
    """获取数据库会话"""
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()
