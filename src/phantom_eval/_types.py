from __future__ import annotations

import json
from pathlib import Path
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field


class ContentTextMessage(BaseModel):
    type: str = "text"
    text: str


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: list[ContentTextMessage]


class Conversation(BaseModel):
    messages: list[Message]
    uid: str = Field(default_factory=lambda: uuid4().hex)

    @staticmethod
    def load_from_path(file_path: str) -> Conversation:
        """
        Load a conversation from a JSON file.

        Args:
            file_path (str): Path to the JSON file.

        Returns:
            Conversation: The conversation object.
        """
        with open(Path(file_path).expanduser()) as f:
            data = json.load(f)

        return Conversation(**data)

    def save_to_path(self, file_path: str) -> None:
        """
        Save the conversation to a JSON file.

        Args:
            file_path (str): Path to the JSON file.
        """
        with open(Path(file_path).expanduser(), "w") as f:
            f.write(self.model_dump_json(indent=4))


class LLMChatResponse(BaseModel):
    pred: str
    usage: dict
    error: str | None = None
