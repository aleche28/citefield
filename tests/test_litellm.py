from types import SimpleNamespace

import pytest
from pydantic import BaseModel

from citefield.llm.base import Message
from citefield.llm.litellm import LiteLLMBackend


class Answer(BaseModel):
    answer: int


@pytest.fixture
def sent(monkeypatch):
    """The keyword arguments of the last `litellm.completion` call, which is faked."""
    import litellm

    calls = {}

    def completion(**kwargs):
        calls.update(kwargs)
        message = SimpleNamespace(content='{"answer": 391}')
        usage = SimpleNamespace(prompt_tokens=10, completion_tokens=5)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)], usage=usage)

    monkeypatch.setattr(litellm, "completion", completion)
    return calls


def call(backend):
    return backend.complete_structured([Message(role="user", content="17*23?")], Answer)


def test_defaults_require_supported_parameters(sent):
    call(LiteLLMBackend("openrouter/google/gemini-3.1-flash-lite"))
    assert sent["temperature"] == 0
    assert sent["extra_body"] == {"provider": {"require_parameters": True}}
    assert "reasoning_effort" not in sent


def test_reasoning_effort_and_provider_routing_are_sent(sent):
    provider = {"order": ["deepinfra/bf16"], "allow_fallbacks": False}
    call(LiteLLMBackend("openrouter/qwen/qwen3.8-27b", reasoning_effort="none", provider=provider))
    assert sent["reasoning_effort"] == "none"
    assert sent["extra_body"] == {"provider": {"require_parameters": True, **provider}}


def test_no_routing_for_other_providers(sent):
    completion = call(LiteLLMBackend("anthropic/claude-haiku-5.5", temperature=None))
    assert "extra_body" not in sent and "temperature" not in sent
    assert (completion.parsed.answer, completion.input_tokens) == (391, 10)
