from __future__ import annotations

import asyncio

from src.config import load_config
from src.conversation import ChatMessage, ConversationManager
from src.llm.ollama_client import OllamaClient
from src.tts.audio_player import play_wav_bytes_async
from src.tts.voicevox_client import VoicevoxClient
from src.twitch_bot import TwitchChatBot


async def main() -> None:
    cfg = load_config()

    llm_client = OllamaClient(model=cfg.llm.model, host=cfg.llm.host)
    tts_client = (
        VoicevoxClient(host=cfg.tts.voicevox_host, speaker=cfg.tts.speaker_id)
        if cfg.tts.enabled
        else None
    )

    manager = ConversationManager(
        persona=cfg.persona.system_prompt,
        generate_reply=llm_client.chat,
        idle_seconds=cfg.behavior.idle_seconds,
        max_deep_dives=cfg.behavior.max_deep_dives,
        history_max_messages=cfg.behavior.history_max_messages,
    )

    async def on_chat_message(author: str, content: str) -> None:
        await manager.on_chat_message(
            ChatMessage(author=author, content=content, timestamp=asyncio.get_event_loop().time())
        )

    bot = TwitchChatBot(
        token=cfg.twitch.token,
        channel=cfg.twitch.channel,
        nick=cfg.twitch.bot_nick,
        on_chat_message=on_chat_message,
    )

    async def on_response(text: str) -> None:
        print(f"[{cfg.persona.name}] {text}")
        await bot.send_message(text)
        if tts_client is not None:
            audio = await tts_client.synthesize_async(text)
            await play_wav_bytes_async(audio)

    await asyncio.gather(bot.start(), manager.run(on_response))


if __name__ == "__main__":
    asyncio.run(main())
