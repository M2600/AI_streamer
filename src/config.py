from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import yaml
from dotenv import load_dotenv


@dataclass
class TwitchConfig:
    token: str
    channel: str
    bot_nick: str


@dataclass
class LLMConfig:
    model: str
    host: str


@dataclass
class TTSConfig:
    enabled: bool
    voicevox_host: str
    speaker_id: int


@dataclass
class PersonaConfig:
    name: str
    system_prompt: str


@dataclass
class BehaviorConfig:
    idle_seconds: float
    max_deep_dives: int
    history_max_messages: int


@dataclass
class AppConfig:
    twitch: TwitchConfig
    llm: LLMConfig
    tts: TTSConfig
    persona: PersonaConfig
    behavior: BehaviorConfig


def load_config(config_path: str | Path = "config.yaml", env_path: str | Path | None = None) -> AppConfig:
    load_dotenv(dotenv_path=env_path)

    with open(config_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    twitch_token = os.environ.get("TWITCH_TOKEN")
    twitch_channel = os.environ.get("TWITCH_CHANNEL")
    twitch_nick = os.environ.get("TWITCH_BOT_NICK") or twitch_channel

    if not twitch_token or not twitch_channel:
        raise RuntimeError(
            "TWITCH_TOKEN と TWITCH_CHANNEL が設定されていません。"
            ".env.example を .env にコピーして値を設定してください。"
        )

    llm_raw = raw.get("llm", {})
    tts_raw = raw.get("tts", {})
    persona_raw = raw.get("persona", {})
    behavior_raw = raw.get("behavior", {})

    if "system_prompt" not in persona_raw:
        raise RuntimeError("config.yaml の persona.system_prompt を設定してください。")

    return AppConfig(
        twitch=TwitchConfig(token=twitch_token, channel=twitch_channel, bot_nick=twitch_nick),
        llm=LLMConfig(
            model=llm_raw.get("model", "llama3"),
            host=llm_raw.get("host", "http://localhost:11434"),
        ),
        tts=TTSConfig(
            enabled=bool(tts_raw.get("enabled", True)),
            voicevox_host=tts_raw.get("voicevox_host", "http://127.0.0.1:50021"),
            speaker_id=int(tts_raw.get("speaker_id", 1)),
        ),
        persona=PersonaConfig(
            name=persona_raw.get("name", "AI"),
            system_prompt=persona_raw["system_prompt"],
        ),
        behavior=BehaviorConfig(
            idle_seconds=float(behavior_raw.get("idle_seconds", 45)),
            max_deep_dives=int(behavior_raw.get("max_deep_dives", 3)),
            history_max_messages=int(behavior_raw.get("history_max_messages", 20)),
        ),
    )
