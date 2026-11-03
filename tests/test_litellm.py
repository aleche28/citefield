from types import SimpleNamespace

import pytest
from pydantic import BaseModel

from citefield.llm.base import Message, UnsupportedSettingError
from citefield.llm.litellm import LiteLLMBackend, check_environment


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


def failing(monkeypatch, exc):
    import litellm

    def completion(**kwargs):
        raise exc

    monkeypatch.setattr(litellm, "completion", completion)


def test_rejected_temperature_says_which_setting_to_change(monkeypatch):
    import litellm

    error = litellm.BadRequestError(
        "temperature is deprecated for this model", model="claude-haiku-5-5", llm_provider="x"
    )
    failing(monkeypatch, error)
    with pytest.raises(UnsupportedSettingError) as exc:
        call(LiteLLMBackend("anthropic/claude-haiku-5-5"))
    assert str(exc.value) == (
        "anthropic/claude-haiku-5-5 doesn't accept temperature; set settings.llm.temperature: null"
    )


def test_openrouter_without_a_provider_for_the_parameters(monkeypatch):
    import litellm

    message = "No endpoints found that can handle the requested parameters."
    failing(monkeypatch, litellm.NotFoundError(message, model="m", llm_provider="openrouter"))
    with pytest.raises(UnsupportedSettingError, match="try settings.llm.temperature: null"):
        call(LiteLLMBackend("openrouter/anthropic/claude-haiku-5.5"))


def test_other_bad_requests_pass_through(monkeypatch):
    import litellm

    error = litellm.BadRequestError("prompt is too long", model="m", llm_provider="x")
    failing(monkeypatch, error)
    with pytest.raises(litellm.BadRequestError):
        call(LiteLLMBackend("anthropic/claude-haiku-5-5"))
    # a parameter we didn't send isn't ours to blame
    error = litellm.BadRequestError("temperature is not supported", model="m", llm_provider="x")
    failing(monkeypatch, error)
    with pytest.raises(litellm.BadRequestError):
        call(LiteLLMBackend("anthropic/claude-haiku-5-5", temperature=None))


@pytest.mark.parametrize(
    ("model", "env", "problems"),
    [
        (
            "anthropic/claude-haiku-5-5",
            {},
            ["ANTHROPIC_API_KEY is not set for anthropic/claude-haiku-5-5"],
        ),
        ("anthropic/claude-haiku-5-5", {"ANTHROPIC_API_KEY": "k"}, []),
        ("gemini/gemini-3-flash", {"GEMINI_API_KEY": "k"}, []),
        (
            "azure_ai/claude-haiku-5-5",
            {},
            [
                "AZURE_AI_API_BASE is not set for azure_ai/claude-haiku-5-5",
                "AZURE_AI_API_KEY is not set for azure_ai/claude-haiku-5-5 "
                "(or AZURE_AD_TOKEN for Entra ID)",
            ],
        ),
        ("azure_ai/claude-haiku-5-5", {"AZURE_AI_API_BASE": "u", "AZURE_AI_API_KEY": "k"}, []),
        ("azure/my-deployment", {"AZURE_API_BASE": "u", "AZURE_AD_TOKEN": "t"}, []),
        ("unknownprovider/some-model", {}, []),  # fails at the first call instead
    ],
)
def test_check_environment(monkeypatch, model, env, problems):
    for name, value in env.items():
        monkeypatch.setenv(name, value)
    assert check_environment(model) == (problems, [])


def test_ollama_without_api_base_only_warns():
    problems, warnings = check_environment("ollama_chat/qwen3")
    assert problems == []
    assert warnings == [
        "OLLAMA_API_BASE is not set for ollama_chat/qwen3; using http://localhost:11434"
    ]
