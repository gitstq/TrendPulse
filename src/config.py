"""
配置管理模块
支持从YAML文件和环境变量加载配置
"""

import os
import yaml
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
from loguru import logger


class AppConfig(BaseModel):
    """应用基础配置"""
    name: str = "TrendPulse"
    version: str = "1.0.0"
    description: str = "智能热点监控分析平台"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000


class MonitorConfig(BaseModel):
    """监控配置"""
    mode: str = "incremental"  # daily / current / incremental
    schedule: str = "0 9 * * *"
    interval: int = 30
    retention_days: int = 30


class KeywordsConfig(BaseModel):
    """关键词配置"""
    focus: List[str] = Field(default_factory=list)
    required: List[str] = Field(default_factory=list)
    exclude: List[str] = Field(default_factory=list)


class PlatformConfig(BaseModel):
    """单个平台配置"""
    enabled: bool = True
    url: str = ""
    priority: int = 1


class PlatformsConfig(BaseModel):
    """平台配置集合"""
    weibo: PlatformConfig = Field(default_factory=lambda: PlatformConfig())
    zhihu: PlatformConfig = Field(default_factory=lambda: PlatformConfig())
    baidu: PlatformConfig = Field(default_factory=lambda: PlatformConfig())
    bilibili: PlatformConfig = Field(default_factory=lambda: PlatformConfig())
    toutiao: PlatformConfig = Field(default_factory=lambda: PlatformConfig())
    douyin: PlatformConfig = Field(default_factory=lambda: PlatformConfig())


class AIConfig(BaseModel):
    """AI分析配置"""
    provider: str = "openai"  # openai / anthropic / local
    api_key: str = ""
    model: str = "gpt-3.5-turbo"
    enable_summary: bool = True
    enable_sentiment: bool = True
    summary_max_length: int = 200


class NotificationChannel(BaseModel):
    """通知渠道配置"""
    enabled: bool = False
    webhook_url: Optional[str] = None
    bot_token: Optional[str] = None
    chat_id: Optional[str] = None
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    to_email: Optional[str] = None


class NotificationsConfig(BaseModel):
    """通知配置集合"""
    wecom: NotificationChannel = Field(default_factory=lambda: NotificationChannel())
    feishu: NotificationChannel = Field(default_factory=lambda: NotificationChannel())
    dingtalk: NotificationChannel = Field(default_factory=lambda: NotificationChannel())
    telegram: NotificationChannel = Field(default_factory=lambda: NotificationChannel())
    email: NotificationChannel = Field(default_factory=lambda: NotificationChannel())


class DatabaseConfig(BaseModel):
    """数据库配置"""
    type: str = "sqlite"
    sqlite_path: str = "./data/trendpulse.db"
    pool_size: int = 5
    max_overflow: int = 10


class LoggingConfig(BaseModel):
    """日志配置"""
    level: str = "INFO"
    format: str = "{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
    file: str = "./logs/trendpulse.log"
    rotation: str = "1 day"
    retention: str = "30 days"


class Settings(BaseSettings):
    """全局配置类"""
    app: AppConfig = Field(default_factory=AppConfig)
    monitor: MonitorConfig = Field(default_factory=MonitorConfig)
    keywords: KeywordsConfig = Field(default_factory=KeywordsConfig)
    platforms: PlatformsConfig = Field(default_factory=PlatformsConfig)
    ai: AIConfig = Field(default_factory=AIConfig)
    notifications: NotificationsConfig = Field(default_factory=NotificationsConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


def load_yaml_config(config_path: str = "config/config.yaml") -> dict:
    """从YAML文件加载配置"""
    path = Path(config_path)
    if not path.exists():
        logger.warning(f"配置文件不存在: {config_path}")
        return {}
    
    with open(path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    
    # 处理环境变量占位符
    config = resolve_env_variables(config)
    return config


def resolve_env_variables(obj):
    """递归解析配置中的环境变量占位符"""
    if isinstance(obj, dict):
        return {k: resolve_env_variables(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [resolve_env_variables(item) for item in obj]
    elif isinstance(obj, str) and obj.startswith("${") and obj.endswith("}"):
        env_var = obj[2:-1]
        default_value = ""
        if ":-" in env_var:
            env_var, default_value = env_var.split(":-", 1)
        return os.getenv(env_var, default_value)
    return obj


def load_settings(config_path: str = "config/config.yaml") -> Settings:
    """加载完整配置"""
    yaml_config = load_yaml_config(config_path)
    
    # 创建Settings实例
    if yaml_config:
        # 使用YAML配置创建Settings
        settings = Settings(**yaml_config)
    else:
        settings = Settings()
    
    return settings


# 全局配置实例
settings = load_settings()
