"""
邮件通知器
"""
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import smtplib
import asyncio

from app.notifier.base import BaseNotifier
from app.config import get_config
from app.models import TrendItem


class EmailNotifier(BaseNotifier):
    """邮件通知器"""
    
    def __init__(self):
        self.config = get_config()
        self.notifier_config = self.config.notifiers.get("email")
    
    @property
    def notifier_type(self) -> str:
        return "email"
    
    def is_enabled(self) -> bool:
        """检查是否启用"""
        if not self.notifier_config:
            return False
        return (
            self.notifier_config.enabled
            and bool(self.notifier_config.smtp_host)
            and bool(self.notifier_config.smtp_user)
            and bool(self.notifier_config.smtp_password)
            and bool(self.notifier_config.to_email)
        )
    
    async def send(self, item: TrendItem) -> bool:
        """发送邮件通知"""
        if not self.is_enabled():
            return False
        
        try:
            # 在异步环境中运行同步的SMTP操作
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._send_sync, item)
            
        except Exception as e:
            print(f"邮件通知发送失败: {e}")
            return False
    
    def _send_sync(self, item: TrendItem) -> bool:
        """同步发送邮件"""
        try:
            # 创建邮件
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"【{item.platform.upper()}】热点推送: {item.title[:50]}"
            msg["From"] = self.notifier_config.smtp_user
            msg["To"] = self.notifier_config.to_email
            
            # 纯文本内容
            text_content = self.format_message(item)
            # HTML内容
            html_content = self._build_html(item)
            
            msg.attach(MIMEText(text_content, "plain", "utf-8"))
            msg.attach(MIMEText(html_content, "html", "utf-8"))
            
            # 连接SMTP服务器
            with smtplib.SMTP(
                self.notifier_config.smtp_host,
                self.notifier_config.smtp_port or 587,
                timeout=30,
            ) as server:
                server.starttls()
                server.login(
                    self.notifier_config.smtp_user,
                    self.notifier_config.smtp_password,
                )
                server.sendmail(
                    self.notifier_config.smtp_user,
                    self.notifier_config.to_email,
                    msg.as_string(),
                )
            
            return True
            
        except Exception as e:
            print(f"邮件发送失败: {e}")
            return False
    
    def _build_html(self, item: TrendItem) -> str:
        """构建HTML邮件内容"""
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #f5f5f5; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                .title {{ font-size: 18px; font-weight: bold; color: #1a1a1a; margin-bottom: 10px; }}
                .content {{ background: #fff; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
                .meta {{ color: #666; font-size: 14px; margin-top: 15px; }}
                .meta-item {{ margin: 5px 0; }}
                .button {{ display: inline-block; padding: 10px 20px; background: #007bff; color: #fff; 
                          text-decoration: none; border-radius: 5px; margin-top: 15px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>🔥 【{item.platform.upper()}】热点推送</h2>
                </div>
                <div class="content">
                    <div class="title">{item.title}</div>
        """
        
        if item.summary:
            html += f'<p>{item.summary}</p>'
        
        html += '<div class="meta">'
        html += f'<div class="meta-item">📊 <strong>热度：</strong>{item.hot_score}</div>'
        
        if item.sentiment:
            html += f'<div class="meta-item">💭 <strong>情感：</strong>{item.sentiment}</div>'
        
        if item.priority:
            html += f'<div class="meta-item">⚡ <strong>优先级：</strong>{item.priority}</div>'
        
        if item.keywords:
            html += f'<div class="meta-item">🏷️ <strong>关键词：</strong>{", ".join(item.keywords[:5])}</div>'
        
        html += '</div>'
        
        if item.url:
            html += f'<a href="{item.url}" class="button">查看详情</a>'
        
        html += """
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    async def send_text(self, subject: str, content: str) -> bool:
        """发送纯文本邮件"""
        if not self.is_enabled():
            return False
        
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._send_text_sync, subject, content)
            
        except Exception as e:
            print(f"邮件发送失败: {e}")
            return False
    
    def _send_text_sync(self, subject: str, content: str) -> bool:
        """同步发送纯文本邮件"""
        try:
            msg = MIMEText(content, "plain", "utf-8")
            msg["Subject"] = subject
            msg["From"] = self.notifier_config.smtp_user
            msg["To"] = self.notifier_config.to_email
            
            with smtplib.SMTP(
                self.notifier_config.smtp_host,
                self.notifier_config.smtp_port or 587,
                timeout=30,
            ) as server:
                server.starttls()
                server.login(
                    self.notifier_config.smtp_user,
                    self.notifier_config.smtp_password,
                )
                server.sendmail(
                    self.notifier_config.smtp_user,
                    self.notifier_config.to_email,
                    msg.as_string(),
                )
            
            return True
            
        except Exception as e:
            print(f"邮件发送失败: {e}")
            return False
