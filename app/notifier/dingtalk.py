"""
钉钉通知器
"""
import base64
import hashlib
import hmac
import time
import urllib.parse
from typing import Optional

import httpx

from app.notifier.base import BaseNotifier
from app.config import get_config
from app.models import TrendItem


class DingtalkNotifier(BaseNotifier):
    """钉钉机器人通知器"""
    
    def __init__(self):
        self.config = get_config()
        self.notifier_config = self.config.notifiers.get("dingtalk")
    
    @property
    def notifier_type(self) -> str:
        return "dingtalk"
    
    def is_enabled(self) -> bool:
        """检查是否启用"""
        if not self.notifier_config:
            return False
        return self.notifier_config.enabled and bool(self.notifier_config.webhook_url)
    
    async def send(self, item: TrendItem) -> bool:
        """发送钉钉通知"""
        if not self.is_enabled():
            return False
        
        try:
            message = self._build_message(item)
            webhook_url = self._get_webhook_url()
            
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    webhook_url,
                    json=message,
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()
                
                result = response.json()
                return result.get("errcode") == 0
                
        except Exception as e:
            print(f"钉钉通知发送失败: {e}")
            return False
    
    def _build_message(self, item: TrendItem) -> dict:
        """构建钉钉消息"""
        return {
            "msgtype": "markdown",
            "markdown": {
                "title": f"【{item.platform.upper()}】热点推送",
                "text": self.format_markdown(item),
            },
        }
    
    def _get_webhook_url(self) -> str:
        """获取带签名的Webhook URL"""
        url = self.notifier_config.webhook_url
        secret = self.notifier_config.secret
        
        if not secret:
            return url
        
        # 生成签名
        timestamp = str(round(time.time() * 1000))
        string_to_sign = f"{timestamp}\n{secret}"
        
        hmac_code = hmac.new(
            secret.encode("utf-8"),
            string_to_sign.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).digest()
        
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
        
        # 拼接URL
        separator = "&" if "?" in url else "?"
        return f"{url}{separator}timestamp={timestamp}&sign={sign}"
    
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
            
            webhook_url = self._get_webhook_url()
            
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    webhook_url,
                    json=message,
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()
                
                result = response.json()
                return result.get("errcode") == 0
                
        except Exception as e:
            print(f"钉钉通知发送失败: {e}")
            return False
