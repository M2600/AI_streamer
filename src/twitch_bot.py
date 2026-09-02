from __future__ import annotations

from typing import Awaitable, Callable

from twitchio.ext import commands

OnChatMessage = Callable[[str, str], Awaitable[None]]


class TwitchChatBot(commands.Bot):
    """Twitchチャットの受信/送信のみを担当するアダプタ。会話ロジックは持たない。"""

    def __init__(self, token: str, channel: str, nick: str, on_chat_message: OnChatMessage) -> None:
        super().__init__(token=token, prefix="!", initial_channels=[channel], nick=nick)
        self._channel_name = channel
        self._on_chat_message = on_chat_message

    async def event_ready(self) -> None:
        print(f"[twitch] logged in as {self.nick}, listening on #{self._channel_name}")

    async def event_message(self, message) -> None:
        if message.echo:
            return
        await self._on_chat_message(message.author.name, message.content)

    async def send_message(self, text: str) -> None:
        channel = self.get_channel(self._channel_name)
        if channel is not None:
            await channel.send(text)
