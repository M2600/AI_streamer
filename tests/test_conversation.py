import asyncio
import contextlib

import pytest

from src.conversation import (
    ChatMessage,
    ConversationManager,
    DEEP_DIVE_INSTRUCTION,
    NEW_TOPIC_INSTRUCTION,
    REACTIVE_INSTRUCTION,
)


def make_manager(**overrides):
    calls = []

    async def fake_generate(messages):
        calls.append(messages)
        instruction = messages[-1]["content"]
        return f"reply-to:{instruction}"

    defaults = dict(
        persona="persona-prompt",
        generate_reply=fake_generate,
        idle_seconds=0.05,
        max_deep_dives=2,
        history_max_messages=20,
    )
    defaults.update(overrides)
    manager = ConversationManager(**defaults)
    return manager, calls


async def run_briefly(manager, on_response, seconds):
    task = asyncio.create_task(manager.run(on_response))
    await asyncio.sleep(seconds)
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task


@pytest.mark.asyncio
async def test_reacts_to_chat_message():
    manager, calls = make_manager(idle_seconds=10)
    responses = []

    async def on_response(text):
        responses.append(text)

    task = asyncio.create_task(manager.run(on_response))
    await manager.on_chat_message(ChatMessage(author="taro", content="hello", timestamp=0))
    await asyncio.sleep(0.05)
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task

    assert len(responses) == 1
    assert calls[0][-1]["content"] == REACTIVE_INSTRUCTION
    assert manager.current_topic == "hello"
    assert manager.history[0] == {"role": "user", "content": "taro: hello"}
    assert manager.history[1]["role"] == "assistant"


@pytest.mark.asyncio
async def test_deep_dives_then_switches_to_new_topic():
    manager, calls = make_manager(idle_seconds=0.03, max_deep_dives=2)
    responses = []

    async def on_response(text):
        responses.append(text)

    await manager.on_chat_message(ChatMessage(author="taro", content="cats", timestamp=0))
    # First iteration handles the chat message; subsequent idle timeouts drive deep dives.
    await run_briefly(manager, on_response, seconds=0.03 * 5)

    instructions = [c[-1]["content"] for c in calls]
    assert instructions[0] == REACTIVE_INSTRUCTION
    # up to max_deep_dives deep dives follow the reactive reply, then a new-topic switch
    first_new_topic = instructions.index(NEW_TOPIC_INSTRUCTION)
    deep_dive_prefix = instructions[1:first_new_topic]
    assert deep_dive_prefix == [DEEP_DIVE_INSTRUCTION] * manager.max_deep_dives


@pytest.mark.asyncio
async def test_idle_with_no_prior_topic_generates_new_topic():
    manager, calls = make_manager(idle_seconds=0.02)
    responses = []

    async def on_response(text):
        responses.append(text)

    await run_briefly(manager, on_response, seconds=0.03)

    assert len(responses) >= 1
    assert calls[0][-1]["content"] == NEW_TOPIC_INSTRUCTION


@pytest.mark.asyncio
async def test_history_is_trimmed_to_max_messages():
    manager, _ = make_manager(idle_seconds=10, history_max_messages=4)

    async def on_response(text):
        pass

    task = asyncio.create_task(manager.run(on_response))
    for i in range(5):
        await manager.on_chat_message(ChatMessage(author="taro", content=f"msg-{i}", timestamp=i))
        await asyncio.sleep(0.02)
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task

    assert len(manager.history) <= 4


@pytest.mark.asyncio
async def test_new_chat_message_resets_deep_dive_state():
    manager, calls = make_manager(idle_seconds=0.02, max_deep_dives=5)
    responses = []

    async def on_response(text):
        responses.append(text)

    task = asyncio.create_task(manager.run(on_response))
    await manager.on_chat_message(ChatMessage(author="taro", content="first topic", timestamp=0))
    await asyncio.sleep(0.05)  # let a couple of deep dives happen
    assert manager.deep_dive_count > 0

    await manager.on_chat_message(ChatMessage(author="hanako", content="second topic", timestamp=1))
    await asyncio.sleep(0.01)

    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task

    assert manager.current_topic == "second topic"
    assert manager.deep_dive_count == 0
