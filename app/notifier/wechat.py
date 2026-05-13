"""
企业微信通知器
"""
import json
from typing import Optional

import httpx

from app.notifier.base import BaseNotifier
from app.config import get_config
from app.models import TrendItem


class WechatNotifier(BaseNotifier):
    """企业微信机器人通知器"""
    
    def __init__(self):
        self.config = get_config()
        self.notifier_config = self.config.notifiers.get("wechat")
    
    @property
    def notifier_type(self) -> str:
        return "wechat"
    
    def is_enabled(self) -> bool:
        """检查是否启用"""
        if not self.notifier_config:
            return False
        return self.notifier_config.enabled and bool(self.notifier_config.webhook_url)
    
    async def send(self, item: TrendItem) -> bool:
        """发送企业微信通知"""
        if not self.is_enabled():
            return False
        
        try:
            message = self._build_message(item)
            
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    self.notifier_config.webhook_url,
                    json=message,
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()
                
                result = response.json()
                return result.get("errcode") == 0
                
        except Exception as e:
            print(f"企业微信通知发送失败: {e}")
            return False
    
    def _build_message(self, item: TrendItem) -> dict:
        """构建企业微信消息"""
        content = self.format_message(item)
        
        # 使用markdown格式
        return {
            "msgtype": "markdown",
            "markdown": {
                "content": self.format_markdown(item),
            },
        }
    
    async def send_text(self, content: str) -> bool:
        """发送纯文本消息"""
        if not self.is_enabled():
            return False
        
        try:
            message = {
                "msgtype": "text",
                "text": {
                    "content": content,
                },
            }
            
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    self.notifier_config.webhook_url,
                    json=message,
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()
                
                result = response.json()
                return result.get("errcode") == 0
                
        except Exception as e:
            print(f"企业微信通知发送失败: {e}")
            return False
