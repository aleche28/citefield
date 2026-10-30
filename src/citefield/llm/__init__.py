"""LLM backends. Third-party backends register through the `citefield.llm_backends` entry point."""

from citefield.llm.base import LLMBackend, Message

__all__ = ["LLMBackend", "Message"]
