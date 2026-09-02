from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Awaitable, Callable, List, Optional

GenerateReply = Callable[[List[dict]], Awaitable[str]]
OnResponse = Callable[[str], Awaitable[None]]

REACTIVE_INSTRUCTION = "視聴者の直前のチャットに短く楽しく反応してください。"
DEEP_DIVE_INSTRUCTION = "チャットが静かです。直前の話題をもう少し深掘りして話を続けてください。"
NEW_TOPIC_INSTRUCTION = (
    "チャットがしばらく静かです。これまでの話題とは違う新しい雑談や実況、"
    "視聴者への質問など、自分から新しい話題を振ってください。"
)


@dataclass
class ChatMessage:
    author: str
    content: str
    timestamp: float


class ConversationManager:
    """チャット反応・話題の深掘り・アイドル時の自発発話を管理する。

    - チャットが来たら反応する
    - チャットが idle_seconds 秒来なければ、直前の話題を深掘りする
    - 深掘りが max_deep_dives 回続いたら、新しい話題に切り替える
    """

    def __init__(
        self,
        persona: str,
        generate_reply: GenerateReply,
        idle_seconds: float = 45,
        max_deep_dives: int = 3,
        history_max_messages: int = 20,
    ) -> None:
        self.persona = persona
        self.generate_reply = generate_reply
        self.idle_seconds = idle_seconds
        self.max_deep_dives = max_deep_dives
        self.history_max_messages = history_max_messages

        self.history: List[dict] = []
        self.current_topic: Optional[str] = None
        self.deep_dive_count = 0

        self._pending: "asyncio.Queue[ChatMessage]" = asyncio.Queue()

    async def on_chat_message(self, message: ChatMessage) -> None:
        await self._pending.put(message)

    async def run(self, on_response: OnResponse) -> None:
        """メインループ。チャット受信 or アイドルタイムアウトを待ち続ける。"""
        while True:
            try:
                message = await asyncio.wait_for(self._pending.get(), timeout=self.idle_seconds)
            except asyncio.TimeoutError:
                await self._handle_idle(on_response)
            else:
                await self._handle_chat(message, on_response)

    async def _handle_chat(self, message: ChatMessage, on_response: OnResponse) -> None:
        self._append("user", f"{message.author}: {message.content}")
        self.current_topic = message.content
        self.deep_dive_count = 0
        reply = await self._generate(REACTIVE_INSTRUCTION)
        await self._emit(reply, on_response)

    async def _handle_idle(self, on_response: OnResponse) -> None:
        if self.current_topic is not None and self.deep_dive_count < self.max_deep_dives:
            self.deep_dive_count += 1
            reply = await self._generate(DEEP_DIVE_INSTRUCTION)
        else:
            self.current_topic = None
            self.deep_dive_count = 0
            reply = await self._generate(NEW_TOPIC_INSTRUCTION)
            self.current_topic = reply
        await self._emit(reply, on_response)

    async def _generate(self, instruction: str) -> str:
        messages = [{"role": "system", "content": self.persona}]
        messages.extend(self.history[-self.history_max_messages :])
        messages.append({"role": "system", "content": instruction})
        reply = await self.generate_reply(messages)
        return reply.strip()

    async def _emit(self, reply: str, on_response: OnResponse) -> None:
        self._append("assistant", reply)
        await on_response(reply)

    def _append(self, role: str, content: str) -> None:
        self.history.append({"role": role, "content": content})
        if len(self.history) > self.history_max_messages:
            self.history = self.history[-self.history_max_messages :]
