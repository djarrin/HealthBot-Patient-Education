from typing import Any, Dict, List, Literal, Optional, TypedDict, Union
from langgraph.graph.message import MessagesState


class MultipleChoiceQuestion(TypedDict):
    question: str
    choices: List[str]
    correct_letter: str


class ConfirmationPrompt(TypedDict):
    message: str
    requires_confirmation: bool


class HealthBotState(MessagesState):
    # User input and workflow control
    user_message: str
    topic: str
    status: Literal[
        "collecting_topic",
        "searching", 
        "summarizing",
        "presenting_summary",
        "awaiting_ready_for_quiz",
        "generating_question",
        "awaiting_answer",
        "evaluating",
        "ask_restart",
        "ended",
    ]
    # Knowledge and content
    search_results: List[Dict[str, Any]]
    summary: str
    citations: List[str]
    # Quiz content
    question: str
    correct_answer: str
    multiple_choice: Optional[MultipleChoiceQuestion]
    # Evaluation
    user_answer: str
    grade: Literal["Correct", "Incorrect"]
    explanation: str
    # Output for the handler to send back to the user
    bot_message: str
    # Special response types for frontend
    response_type: Literal["text", "confirmation", "multiple_choice"]
    confirmation_prompt: Optional[ConfirmationPrompt]
