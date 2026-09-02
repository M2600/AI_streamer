from __future__ import annotations

from typing import List

import ollama


class OllamaClient:
    """ローカルで動くOllamaサーバーに会話生成をリクエストするクライアント。"""

    def __init__(self, model: str, host: str = "http://localhost:11434") -> None:
        self.model = model
        self._client = ollama.AsyncClient(host=host)

    async def chat(self, messages: List[dict]) -> str:
        response = await self._client.chat(model=self.model, messages=messages)
        return response["message"]["content"]
