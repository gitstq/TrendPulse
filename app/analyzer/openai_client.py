"""
OpenAI客户端
"""
import json
from typing import Optional, Dict, Any

import openai

from app.config import get_config


class OpenAIClient:
    """OpenAI API客户端"""
    
    def __init__(self):
        self.config = get_config().ai
        self._client: Optional[openai.AsyncOpenAI] = None
    
    @property
    def client(self) -> openai.AsyncOpenAI:
        """获取OpenAI客户端"""
        if self._client is None:
            kwargs = {
                "api_key": self.config.api_key,
            }
            if self.config.base_url:
                kwargs["base_url"] = self.config.base_url
            
            self._client = openai.AsyncOpenAI(**kwargs)
        
        return self._client
    
    async def chat_completion(
        self,
        messages: list,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        response_format: Optional[Dict[str, str]] = None,
    ) -> str:
        """
        发送聊天完成请求
        
        Args:
            messages: 消息列表
            model: 模型名称
            temperature: 温度
            max_tokens: 最大token数
            response_format: 响应格式
            
        Returns:
            响应内容
        """
        kwargs = {
            "model": model or self.config.model,
            "messages": messages,
            "temperature": temperature if temperature is not None else self.config.temperature,
            "max_tokens": max_tokens or self.config.max_tokens,
        }
        
        if response_format:
            kwargs["response_format"] = response_format
        
        response = await self.client.chat.completions.create(**kwargs)
        return response.choices[0].message.content
    
    async def analyze_text(
        self,
        text: str,
        system_prompt: str,
        json_mode: bool = False,
    ) -> str:
        """
        分析文本
        
        Args:
            text: 要分析的文本
            system_prompt: 系统提示词
            json_mode: 是否使用JSON模式
            
        Returns:
            分析结果
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text},
        ]
        
        response_format = {"type": "json_object"} if json_mode else None
        
        return await self.chat_completion(
            messages=messages,
            response_format=response_format,
        )
    
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            if not self.config.api_key:
                return False
            
            # 发送一个简单的请求
            response = await self.client.chat.completions.create(
                model=self.config.model,
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=5,
            )
            return True
        except Exception:
            return False
