"""
Response types and utilities for the HealthBot frontend integration.
"""

from typing import Dict, Any, List, Literal, Optional, TypedDict


class MultipleChoiceQuestion(TypedDict):
    """Multiple choice question structure for the frontend."""
    question: str
    choices: List[str]
    correct_letter: str


class ConfirmationPrompt(TypedDict):
    """Confirmation prompt structure for the frontend."""
    message: str
    requires_confirmation: bool


class BotResponse(TypedDict):
    """Complete bot response structure."""
    content: str
    messageId: str
    timestamp: str
    status: str
    responseType: Literal["text", "confirmation", "multiple_choice"]
    multipleChoice: Optional[MultipleChoiceQuestion]
    confirmationPrompt: Optional[ConfirmationPrompt]


def create_text_response(
    content: str,
    message_id: str,
    timestamp: str,
    status: str
) -> BotResponse:
    """Create a text-only response."""
    return {
        "content": content,
        "messageId": message_id,
        "timestamp": timestamp,
        "status": status,
        "responseType": "text",
        "multipleChoice": None,
        "confirmationPrompt": None
    }


def create_confirmation_response(
    content: str,
    message_id: str,
    timestamp: str,
    status: str,
    confirmation_prompt: ConfirmationPrompt
) -> BotResponse:
    """Create a confirmation prompt response."""
    return {
        "content": content,
        "messageId": message_id,
        "timestamp": timestamp,
        "status": status,
        "responseType": "confirmation",
        "multipleChoice": None,
        "confirmationPrompt": confirmation_prompt
    }


def create_multiple_choice_response(
    content: str,
    message_id: str,
    timestamp: str,
    status: str,
    multiple_choice: MultipleChoiceQuestion
) -> BotResponse:
    """Create a multiple choice question response."""
    return {
        "content": content,
        "messageId": message_id,
        "timestamp": timestamp,
        "status": status,
        "responseType": "multiple_choice",
        "multipleChoice": multiple_choice,
        "confirmationPrompt": None
    }
