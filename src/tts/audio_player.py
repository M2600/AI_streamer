from __future__ import annotations

import asyncio
import io

import sounddevice as sd
import soundfile as sf


def play_wav_bytes(data: bytes) -> None:
    audio, samplerate = sf.read(io.BytesIO(data))
    sd.play(audio, samplerate)
    sd.wait()


async def play_wav_bytes_async(data: bytes) -> None:
    await asyncio.to_thread(play_wav_bytes, data)
