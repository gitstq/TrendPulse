"""
通知器基类
"""
from abc import ABC, abstractmethod
from typing import Optional

from app.models import TrendItem


class BaseNotifier(ABC):
    """通知器基类"""
    
    def __init__(self):
        pass
    
    @property
    @abstractmethod
    def notifier_type(self) -> str:
        """通知器类型"""
        pass
    
    @abstractmethod
    async def send(self, item: TrendItem) -> bool:
        """
        发送通知
        
        Args:
            item: 热点数据
            
        Returns:
            是否发送成功
        """
        pass
    
    @abstractmethod
    def is_enabled(self) -> bool:
        """
        检查是否启用
        
        Returns:
            是否启用
        """
        pass
    
    def format_message(self, item: TrendItem) -> str:
        """
        格式化消息
        
        Args:
            item: 热点数据
            
        Returns:
            格式化后的消息
        """
        # 构建消息
        lines = [
            f"🔥 【{item.platform.upper()}】热点推送",
            "",
            f"📌 {item.title}",
        ]
        
        if item.summary:
            lines.append(f"📝 {item.summary[:100]}..." if len(item.summary) > 100 else f"📝 {item.summary}")
        
        lines.append(f"📊 热度：{item.hot_score}")
        
        if item.sentiment:
            sentiment_emoji = {
                "positive": "😊",
                "negative": "😔",
                "neutral": "😐",
                "mixed": "🤔",
            }.get(item.sentiment, "😐")
            lines.append(f"{sentiment_emoji} 情感：{item.sentiment}")
        
        if item.priority:
            priority_emoji = {
                "high": "🔴",
                "medium": "🟡",
                "low": "🟢",
            }.get(item.priority, "⚪")
            lines.append(f"{priority_emoji} 优先级：{item.priority}")
        
        if item.keywords:
            lines.append(f"🏷️ 关键词：{', '.join(item.keywords[:5])}")
        
        if item.url:
            lines.extend(["", f"🔗 {item.url}"])
        
        return "\n".join(lines)
    
    def format_markdown(self, item: TrendItem) -> str:
        """
        格式化Markdown消息
        
        Args:
            item: 热点数据
            
        Returns:
            Markdown格式的消息
        """
        lines = [
            f"## 🔥 【{item.platform.upper()}】热点推送",
            "",
            f"**{item.title}**",
        ]
        
        if item.summary:
            lines.append(f"> {item.summary[:150]}..." if len(item.summary) > 150 else f"> {item.summary}")
        
        lines.append(f"")
        lines.append(f"- 📊 **热度**：{item.hot_score}")
        
        if item.sentiment:
            lines.append(f"- 💭 **情感**：{item.sentiment}")
        
        if item.priority:
            lines.append(f"- ⚡ **优先级**：{item.priority}")
        
        if item.keywords:
            lines.append(f"- 🏷️ **关键词**：{', '.join(item.keywords[:5])}")
        
        if item.url:
            lines.extend(["", f"[查看详情]({item.url})"])
        
        return "\n".join(lines)
