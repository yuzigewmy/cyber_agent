from __future__ import annotations

import os
from dataclasses import dataclass

import httpx


@dataclass
class LLMResult:
    content: str
    provider: str = "fallback"
    error: str | None = None


class LLMClient:
    """Adapter for Qwen chat models through DashScope compatible mode."""

    def __init__(self, model: str | None = None, base_url: str | None = None) -> None:
        self.api_key = os.getenv("DASHSCOPE_API_KEY", "").strip()
        self.model = model or os.getenv("QWEN_MODEL", "qwen-plus")
        self.base_url = (
            base_url
            or os.getenv(
                "QWEN_BASE_URL",
                "https://dashscope.aliyuncs.com/compatible-mode/v1",
            )
        ).rstrip("/")
        self._init_error: str | None = None

        if not self.api_key:
            self._init_error = "DASHSCOPE_API_KEY is not configured."

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def invoke(self, system: str, user: str) -> LLMResult:
        if not self.api_key:
            return LLMResult(
                content=(
                    "千问大模型未启用，当前返回本地规则引擎结果。"
                    "请确认 DASHSCOPE_API_KEY、QWEN_MODEL、QWEN_BASE_URL 配置是否正确。"
                ),
                provider="fallback",
                error=self._init_error,
            )

        try:
            response = httpx.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "temperature": 0.1,
                    "messages": [
                        {
                            "role": "system",
                            "content": system,
                        },
                        {
                            "role": "user",
                            "content": user,
                        },
                    ],
                },
                timeout=60,
            )
            response.raise_for_status()
            payload = response.json()
            content = payload["choices"][0]["message"]["content"]

            return LLMResult(
                content=str(content).strip(),
                provider="qwen",
            )
        except Exception as exc:
            return LLMResult(
                content=(
                    "千问大模型调用失败，已回退到本地规则引擎结果。"
                    "请检查 API Key、模型名、Base URL、网络连通性和账户额度。"
                ),
                provider="fallback",
                error=str(exc),
            )
