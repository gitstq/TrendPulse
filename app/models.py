"""
数据模型定义
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, String, DateTime, Text, Float, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class SentimentType(str, Enum):
    """情感类型"""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    MIXED = "mixed"


class PriorityType(str, Enum):
    """优先级类型"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TrendItemDB(Base):
    """热点数据数据库模型"""
    __tablename__ = "trend_items"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False, index=True)
    url = Column(String(1000), nullable=True)
    platform = Column(String(50), nullable=False, index=True)
    hot_score = Column(Integer, default=0)
    category = Column(String(100), nullable=True)
    author = Column(String(200), nullable=True)
    summary = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    
    # AI分析结果
    sentiment = Column(String(20), nullable=True)
    sentiment_score = Column(Float, nullable=True)
    keywords = Column(JSON, default=list)
    analysis_result = Column(Text, nullable=True)
    priority = Column(String(20), nullable=True)
    
    # 元数据
    raw_data = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    analyzed_at = Column(DateTime(timezone=True), nullable=True)
    notified = Column(Boolean, default=False)
    notified_at = Column(DateTime(timezone=True), nullable=True)


class TrendItem(BaseModel):
    """热点数据Pydantic模型"""
    id: Optional[int] = None
    title: str
    url: Optional[str] = None
    platform: str
    hot_score: int = 0
    category: Optional[str] = None
    author: Optional[str] = None
    summary: Optional[str] = None
    content: Optional[str] = None
    
    # AI分析结果
    sentiment: Optional[SentimentType] = None
    sentiment_score: Optional[float] = None
    keywords: List[str] = Field(default_factory=list)
    analysis_result: Optional[str] = None
    priority: Optional[PriorityType] = None
    
    # 元数据
    raw_data: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    analyzed_at: Optional[datetime] = None
    notified: bool = False
    notified_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class TrendItemCreate(BaseModel):
    """创建热点数据模型"""
    title: str
    url: Optional[str] = None
    platform: str
    hot_score: int = 0
    category: Optional[str] = None
    author: Optional[str] = None
    summary: Optional[str] = None
    content: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None


class TrendItemUpdate(BaseModel):
    """更新热点数据模型"""
    sentiment: Optional[SentimentType] = None
    sentiment_score: Optional[float] = None
    keywords: Optional[List[str]] = None
    analysis_result: Optional[str] = None
    priority: Optional[PriorityType] = None
    analyzed_at: Optional[datetime] = None
    notified: Optional[bool] = None
    notified_at: Optional[datetime] = None


class AnalysisResult(BaseModel):
    """AI分析结果模型"""
    sentiment: SentimentType
    sentiment_score: float = Field(..., ge=-1.0, le=1.0)
    keywords: List[str]
    summary: str
    trends: str
    priority: PriorityType


class CrawlerStatus(BaseModel):
    """爬虫状态模型"""
    platform: str
    enabled: bool
    last_run: Optional[datetime] = None
    last_success: Optional[datetime] = None
    items_count: int = 0
    error_count: int = 0
    status: str = "idle"  # idle, running, error


class NotificationLog(BaseModel):
    """通知日志模型"""
    id: Optional[int] = None
    trend_item_id: int
    notifier_type: str
    status: str  # success, failed
    message: Optional[str] = None
    created_at: Optional[datetime] = None


class DashboardStats(BaseModel):
    """仪表盘统计数据"""
    total_items: int
    today_items: int
    analyzed_items: int
    notified_items: int
    platform_distribution: Dict[str, int]
    sentiment_distribution: Dict[str, int]
    recent_items: List[TrendItem]


class CrawlTask(BaseModel):
    """爬虫任务模型"""
    platform: str
    schedule: Optional[str] = None
    enabled: bool = True


class SystemStatus(BaseModel):
    """系统状态模型"""
    version: str
    uptime: str
    database_connected: bool
    scheduler_running: bool
    active_crawlers: int
    total_crawlers: int
    last_crawl_time: Optional[datetime] = None
