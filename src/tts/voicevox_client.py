from __future__ import annotations

import asyncio

import requests


class VoicevoxClient:
    """ローカルで動くVOICEVOXエンジンに音声合成をリクエストするクライアント。"""

    def __init__(self, host: str = "http://127.0.0.1:50021", speaker: int = 1) -> None:
        self.host = host.rstrip("/")
        self.speaker = speaker

    def synthesize(self, text: str) -> bytes:
        query_res = requests.post(
            f"{self.host}/audio_query",
            params={"text": text, "speaker": self.speaker},
            timeout=30,
        )
        query_res.raise_for_status()

        synth_res = requests.post(
            f"{self.host}/synthesis",
            params={"speaker": self.speaker},
            json=query_res.json(),
            timeout=60,
        )
        synth_res.raise_for_status()
        return synth_res.content

    async def synthesize_async(self, text: str) -> bytes:
        return await asyncio.to_thread(self.synthesize, text)
