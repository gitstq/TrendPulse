"""
配置管理模块
"""
import os
import yaml
from pathlib import Path
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class AppConfig(BaseModel):
    """应用配置"""
    name: str = "TrendPulse"
    version: str = "1.0.0"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8080
    secret_key: str = "change-me-in-production"


class DatabaseConfig(BaseModel):
    """数据库配置"""
    url: str = "sqlite:///./data/trendpulse.db"


class AIConfig(BaseModel):
    """AI配置"""
    provider: str = "openai"
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: str = "gpt-3.5-turbo"
    temperature: float = 0.7
    max_tokens: int = 2000


class CrawlerConfig(BaseModel):
    """爬虫配置"""
    delay: int = 2
    timeout: int = 30
    retries: int = 3
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"


class PlatformConfig(BaseModel):
    """平台配置"""
    enabled: bool = True
    url: str = ""
    limit: int = 50


class NotifierConfig(BaseModel):
    """通知器配置"""
    enabled: bool = False
    webhook_url: Optional[str] = None
    secret: Optional[str] = None
    bot_token: Optional[str] = None
    chat_id: Optional[str] = None
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    to_email: Optional[str] = None


class SchedulerConfig(BaseModel):
    """定时任务配置"""
    default_schedule: str = "*/30 * * * *"
    run_on_startup: bool = True
    timezone: str = "Asia/Shanghai"


class AnalysisConfig(BaseModel):
    """分析配置"""
    enabled: bool = True
    min_hot_score: int = 100
    prompt_template: str = """请对以下热点话题进行深度分析：

标题：{title}
平台：{platform}
热度：{hot_score}

请从以下几个方面分析：
1. 话题背景与核心内容
2. 舆论情感倾向（正面/负面/中性）
3. 可能的发展趋势
4. 相关关键词
5. 建议关注程度（高/中/低）
"""


class Settings(BaseSettings):
    """应用设置"""
    app: AppConfig = Field(default_factory=AppConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    ai: AIConfig = Field(default_factory=AIConfig)
    crawler: CrawlerConfig = Field(default_factory=CrawlerConfig)
    platforms: Dict[str, PlatformConfig] = Field(default_factory=dict)
    notifiers: Dict[str, NotifierConfig] = Field(default_factory=dict)
    scheduler: SchedulerConfig = Field(default_factory=SchedulerConfig)
    analysis: AnalysisConfig = Field(default_factory=AnalysisConfig)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


def load_config(config_path: Optional[str] = None) -> Settings:
    """
    加载配置文件
    
    优先级：环境变量 > 配置文件 > 默认值
    """
    settings = Settings()
    
    # 查找配置文件
    if config_path is None:
        possible_paths = [
            Path("config.yaml"),
            Path("config.yml"),
            Path.home() / ".trendpulse" / "config.yaml",
            Path("/etc/trendpulse/config.yaml"),
        ]
        for path in possible_paths:
            if path.exists():
                config_path = str(path)
                break
    
    # 加载YAML配置
    if config_path and Path(config_path).exists():
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f)
        
        if config_data:
            # 更新配置
            if "app" in config_data:
                settings.app = AppConfig(**config_data["app"])
            if "database" in config_data:
                settings.database = DatabaseConfig(**config_data["database"])
            if "ai" in config_data:
                settings.ai = AIConfig(**config_data["ai"])
            if "crawler" in config_data:
                settings.crawler = CrawlerConfig(**config_data["crawler"])
            if "platforms" in config_data:
                settings.platforms = {
                    k: PlatformConfig(**v) for k, v in config_data["platforms"].items()
                }
            if "notifiers" in config_data:
                settings.notifiers = {
                    k: NotifierConfig(**v) for k, v in config_data["notifiers"].items()
                }
            if "scheduler" in config_data:
                settings.scheduler = SchedulerConfig(**config_data["scheduler"])
            if "analysis" in config_data:
                settings.analysis = AnalysisConfig(**config_data["analysis"])
    
    # 从环境变量覆盖
    if os.getenv("TRENDPULSE_AI_API_KEY"):
        settings.ai.api_key = os.getenv("TRENDPULSE_AI_API_KEY")
    if os.getenv("TRENDPULSE_AI_PROVIDER"):
        settings.ai.provider = os.getenv("TRENDPULSE_AI_PROVIDER")
    if os.getenv("TRENDPULSE_AI_MODEL"):
        settings.ai.model = os.getenv("TRENDPULSE_AI_MODEL")
    if os.getenv("TRENDPULSE_DB_URL"):
        settings.database.url = os.getenv("TRENDPULSE_DB_URL")
    if os.getenv("TRENDPULSE_SECRET_KEY"):
        settings.app.secret_key = os.getenv("TRENDPULSE_SECRET_KEY")
    
    return settings


# 全局配置实例
_config: Optional[Settings] = None


def get_config() -> Settings:
    """获取配置实例（单例模式）"""
    global _config
    if _config is None:
        _config = load_config()
    return _config


def reload_config(config_path: Optional[str] = None) -> Settings:
    """重新加载配置"""
    global _config
    _config = load_config(config_path)
    return _config
