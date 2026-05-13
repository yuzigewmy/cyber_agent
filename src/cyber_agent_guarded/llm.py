from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class LLMResult:
    content: str
    provider: str = "fallback"
    error: str | None = None


class LLMClient:
    """Thin LLM adapter for OpenAI-compatible chat models.

    Environment variables:
      OPENAI_API_KEY      Required for model calls.
      OPENAI_MODEL        Default: gpt-4o-mini
      OPENAI_BASE_URL     Optional. Use this for OpenAI-compatible gateways.
    """

    def __init__(self, model: str | None = None, base_url: str | None = None) -> None:
        self.api_key = os.getenv("OPENAI_API_KEY", "").strip()
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL", "").strip() or None
        self._chat_model = None
        self._init_error: str | None = None

        if not self.api_key:
            self._init_error = "OPENAI_API_KEY is not configured."
            return

        try:
            from langchain_openai import ChatOpenAI  # type: ignore

            kwargs = {
                "model": self.model,
                "temperature": 0.1,
                "api_key": self.api_key,
            }

            if self.base_url:
                kwargs["base_url"] = self.base_url

            self._chat_model = ChatOpenAI(**kwargs)
        except Exception as exc:
            self._chat_model = None
            self._init_error = f"Failed to initialize ChatOpenAI: {exc}"

    @property
    def available(self) -> bool:
        return self._chat_model is not None

    def invoke(self, system: str, user: str) -> LLMResult:
        if self._chat_model is None:
            return LLMResult(
                content=(
                    "大模型未启用，当前返回本地规则引擎结果。"
                    "请确认 OPENAI_API_KEY、OPENAI_MODEL、OPENAI_BASE_URL 配置是否正确。"
                ),
                provider="fallback",
                error=self._init_error,
            )

        try:
            response = self._chat_model.invoke(
                [
                    {
                        "role": "system",
                        "content": system,
                    },
                    {
                        "role": "user",
                        "content": user,
                    },
                ]
            )

            content = getattr(response, "content", "")
            if isinstance(content, list):
                content = "\n".join(str(item) for item in content)

            return LLMResult(
                content=str(content).strip(),
                provider="openai",
            )
        except Exception as exc:
            return LLMResult(
                content=(
                    "大模型调用失败，已回退到本地规则引擎结果。"
                    "请检查 API Key、模型名、Base URL、网络连通性和账户余额。"
                ),
                provider="fallback",
                error=str(exc),
            )