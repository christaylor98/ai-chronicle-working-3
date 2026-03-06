"""Adapters for ingesting various file formats into the knowledge graph."""

from .chatgpt_json_adapter import ChatGPTJsonAdapter, ChatGPTChunk

__all__ = ['ChatGPTJsonAdapter', 'ChatGPTChunk']
