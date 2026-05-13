"""
Telegram通知器
"""
from typing import Optional

import httpx

from app.notifier.base import BaseNotifier
from app.config import get_config
from app.models import TrendItem


class TelegramNotifier(BaseNotifier):
    """Telegram Bot通知器"""
    
    def __init__(self):
        self.config = get_config()
        self.notifier_config = self.config.notifiers.get("telegram")
    
    @property
    def notifier_type(self) -> str:
        return "telegram"
    
    def is_enabled(self) -> bool:
        """检查是否启用"""
        if not self.notifier_config:
            return False
        return (
            self.notifier_config.enabled
            and bool(self.notifier_config.bot_token)
            and bool(self.notifier_config.chat_id)
        )
    
    async def send(self, item: TrendItem) -> bool:
        """发送Telegram通知"""
        if not self.is_enabled():
            return False
        
        try:
            message = self.format_message(item)
            
            api_url = f"https://api.telegram.org/bot{self.notifier_config.bot_token}/sendMessage"
            
            payload = {
                "chat_id": self.notifier_config.chat_id,
                "text": message,
                "parse_mode": "HTML",
                "disable_web_page_preview": False,
            }
            
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(api_url, json=payload)
                response.raise_for_status()
                
                result = response.json()
                return result.get("ok", False)
                
        except Exception as e:
            print(f"Telegram通知发送失败: {e}")
            return False
    
    def format_message(self, item: TrendItem) -> str:
        """格式化HTML消息"""
        lines = [
            f"<b>🔥 【{item.platform.upper()}】热点推送</b>",
            "",
            f"<b>{self._escape_html(item.title)}</b>",
        ]
        
        if item.summary:
            summary = item.summary[:150] + "..." if len(item.summary) > 150 else item.summary
            lines.append(f"<i>{self._escape_html(summary)}</i>")
        
        lines.append(f"")
        lines.append(f"📊 <b>热度</b>：{item.hot_score}")
        
        if item.sentiment:
            lines.append(f"💭 <b>情感</b>：{item.sentiment}")
        
        if item.priority:
            lines.append(f"⚡ <b>优先级</b>：{item.priority}")
        
        if item.keywords:
            keywords_str = ", ".join(item.keywords[:5])
            lines.append(f"🏷️ <b>关键词</b>：{self._escape_html(keywords_str)}")
        
        if item.url:
            lines.extend(["", f'<a href="{item.url}">查看详情</a>'])
        
        return "\n".join(lines)
    
    def _escape_html(self, text: str) -> str:
        """转义HTML特殊字符"""
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )
    
    async def send_text(self, content: str) -> bool:
        """发送纯文本消息"""
        if not self.is_enabled():
            return False
        
        try:
            api_url = f"https://api.telegram.org/bot{self.notifier_config.bot_token}/sendMessage"
            
            payload = {
                "chat_id": self.notifier_config.chat_id,
                "text": content,
                "parse_mode": "HTML",
            }
            
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(api_url, json=payload)
                response.raise_for_status()
                
                result = response.json()
                return result.get("ok", False)
                
        except Exception as e:
            print(f"Telegram通知发送失败: {e}")
            return False
