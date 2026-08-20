"""
LLM客户端封装
通过 UnifiedLLMClient (LiteLLM) 支持多提供商
保留原始 LLMClient 接口以向后兼容
"""

import json
import re
from typing import Optional, Dict, Any, List

from ..config import Config
from ..services.llm_client import UnifiedLLMClient


class LLMClient:
    """
    LLM客户端 - 向后兼容包装器

    内部委托给 UnifiedLLMClient（基于 LiteLLM），
    支持 OpenAI、Anthropic、DeepSeek 等多种提供商。
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None
    ):
        self.api_key = api_key or Config.LLM_API_KEY
        self.base_url = base_url or Config.LLM_BASE_URL
        self.model = model or Config.LLM_MODEL_NAME

        if not self.api_key:
            raise ValueError("LLM_API_KEY 未配置")

        # Delegate to the unified client
        self._unified = UnifiedLLMClient(
            api_key=self.api_key,
            base_url=self.base_url,
            model_name=self.model,
        )

        # Keep a raw OpenAI client for any code that accesses .client directly
        self.client = self._unified.openai_compatible_client

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: Optional[Dict] = None
    ) -> str:
        """
        发送聊天请求

        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大token数
            response_format: 响应格式（如JSON模式）

        Returns:
            模型响应文本
        """
        content = self._unified.chat(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format=response_format if response_format else None,
        )
        # 部分模型（如MiniMax M2.5）会在content中包含<think>思考内容，需要移除
        content = re.sub(r'<think>[\s\S]*?</think>', '', content).strip()
        return content

    def chat_json(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 4096
    ) -> Dict[str, Any]:
        """
        发送聊天请求并返回JSON

        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大token数

        Returns:
            解析后的JSON对象
        """
        try:
            return self._unified.chat_json(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except ValueError:
            # Re-raise with the original error message format for compatibility
            raise

