from __future__ import annotations

import os
from typing import Any, Dict, List, Literal, Optional, TypedDict

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.graph import StateGraph, END
from langgraph_checkpoint_dynamodb import DynamoDBSaver, DynamoDBConfig, DynamoDBTableConfig


class HealthBotState(TypedDict, total=False):
    # Conversation control/status
    status: Literal[
        "collecting_topic",
        "searching",
        "summarizing",
        "presenting_summary",
        "awaiting_ready_for_quiz",
        "generating_question",
        "awaiting_answer",
        "evaluating",
        "presenting_grade",
        "ask_restart",
        "ended",
    ]
    # Inputs and transient fields
    user_message: str
    topic: str
    # Knowledge and content
    search_results: List[Dict[str, Any]]
    summary: str
    citations: List[str]
    # Quiz content
    question: str
    correct_answer: str
    # Evaluation
    user_answer: str
    grade: Literal["Correct", "Incorrect"]
    explanation: str
    # Output for the handler to send back to the user
    bot_message: str


def _get_llm() -> ChatOpenAI:
    # Reads OPENAI_API_KEY from env implicitly
    # Keep a small, fast model for lambda latency
    return ChatOpenAI(model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"), temperature=0)


def _get_tavily() -> TavilySearchResults:
    # Reads TAVILY_API_KEY from env (the tool handles this internally)
    return TavilySearchResults(max_results=5)


def node_collect_topic(state: HealthBotState) -> HealthBotState:
    user_message = (state.get("user_message") or "").strip()
    next_state: HealthBotState = {
        **state,
        "topic": user_message,
        "status": "searching",
        "bot_message": "Got it. I will search for trusted, up-to-date information on: "
        f"{user_message}"
    }
    # Clear consumed user input so downstream router won't over-advance
    next_state["user_message"] = ""
    return next_state


def node_search(state: HealthBotState) -> HealthBotState:
    tavily = _get_tavily()
    topic = state.get("topic", "").strip()
    results = tavily.run(topic)
    # Normalize to a list of dicts we can cite later
    normalized: List[Dict[str, Any]] = []
    for r in results:
        # Each result typically includes: {"url", "content", "title"}
        url = r.get("url") or r.get("source")
        title = r.get("title") or ""
        content = r.get("content") or r.get("snippet") or ""
        normalized.append({"url": url, "title": title, "content": content})

    return {
        **state,
        "search_results": normalized,
        "status": "summarizing",
        "bot_message": "Found sources. Summarizing in plain language...",
    }


def node_summarize(state: HealthBotState) -> HealthBotState:
    llm = _get_llm()
    topic = state.get("topic", "")
    results: List[Dict[str, Any]] = state.get("search_results", [])

    sources_block = "\n\n".join(
        [f"Source: {r.get('title','').strip()} — {r.get('url','').strip()}\n{(r.get('content','') or '')[:1500]}" for r in results]
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "You are a careful medical educator. Write at a 7th–9th grade reading level. Include citations as [n] referencing the sources list order."),
            ("human", (
                "Summarize the most relevant, evidence-based information for a patient about the topic: '{topic}'.\n"
                "- Be accurate and neutral; avoid giving medical advice.\n"
                "- Use short paragraphs and bullets where helpful.\n"
                "- Add a short 'Key Points' list.\n"
                "- Include in-text citation markers like [1], [2] that map to the sources list order below.\n\n"
                "Sources (ordered):\n{sources}\n"
            )),
        ]
    )

    summary = llm.invoke(prompt.format_messages(topic=topic, sources=sources_block)).content

    # Build citations as ordered list of URLs
    citations = [r.get("url", "") for r in results if r.get("url")]

    return {
        **state,
        "summary": summary,
        "citations": citations,
        "status": "presenting_summary",
        "bot_message": summary + "\n\nWhen you're ready for a quick comprehension check, reply 'ready'.",
    }


def node_present_summary(state: HealthBotState) -> HealthBotState:
    # Transition to awaiting user signal
    return {**state, "status": "awaiting_ready_for_quiz"}


def node_generate_question(state: HealthBotState) -> HealthBotState:
    llm = _get_llm()
    summary = state.get("summary", "")
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "Generate a single multiple-choice question (A-D) that checks understanding of the summary."),
            ("human", (
                "Based on the following educational summary, create ONE multiple-choice question with 4 choices (A-D) and mark the correct answer.\n"
                "Return strict JSON with keys: question, choices (list of 4 strings), correct_letter (A-D).\n\n"
                "Summary:\n{summary}"
            )),
        ]
    )

    raw = llm.invoke(prompt.format_messages(summary=summary)).content

    # Be defensive parsing JSON; if bad, fallback to a simple question
    import json
    try:
        parsed = json.loads(raw)
        question = parsed.get("question", "")
        choices = parsed.get("choices", [])
        correct_letter = (parsed.get("correct_letter", "").strip() or "A").upper()
        if not question or len(choices) != 4:
            raise ValueError("Invalid question format")
        correct_index = ["A", "B", "C", "D"].index(correct_letter)
        correct_answer = choices[correct_index]
        formatted = question + "\n" + "\n".join([f"{letter}. {text}" for letter, text in zip(["A","B","C","D"], choices)])
    except Exception:
        # Fallback
        question = "What is one key point from the summary?"
        choices = [
            "A short statement that aligns with the summary",
            "An unrelated claim",
            "A contradictory claim",
            "An extreme or unsafe recommendation",
        ]
        correct_answer = choices[0]
        formatted = question + "\n" + "\n".join([f"{letter}. {text}" for letter, text in zip(["A","B","C","D"], choices)])

    new_state: HealthBotState = {
        **state,
        "question": formatted,
        "correct_answer": correct_answer,
        "status": "awaiting_answer",
        "bot_message": formatted + "\n\nReply with A, B, C, or D.",
    }
    # Clear consumed user input (e.g., 'ready') to create a breakpoint
    new_state["user_message"] = ""
    return new_state


def node_evaluate(state: HealthBotState) -> HealthBotState:
    llm = _get_llm()
    user_message = (state.get("user_message") or "").strip()
    summary = state.get("summary", "")
    citations = state.get("citations", [])
    correct_answer = state.get("correct_answer", "")

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "Evaluate a student's multiple-choice answer strictly against the provided correct answer and summary."),
            ("human", (
                "Student answer: {answer}\n"
                "Correct answer: {correct}\n\n"
                "Summary (with citations markers):\n{summary}\n\n"
                "Return strict JSON with keys: grade ('Correct'|'Incorrect'), explanation (2-4 sentences). Use citations [n] where relevant."
            )),
        ]
    )
    raw = llm.invoke(
        prompt.format_messages(answer=user_message, correct=correct_answer, summary=summary)
    ).content

    import json
    try:
        parsed = json.loads(raw)
        grade = parsed.get("grade", "Incorrect")
        explanation = parsed.get("explanation", "")
    except Exception:
        grade = "Correct" if user_message.lower().startswith("a") else "Incorrect"
        explanation = (
            "Thanks for your answer. Based on the material above, here is an explanation with citations: "
            + " ".join([f"[{i+1}] {url}" for i, url in enumerate(citations[:3])])
        )

    message = f"Grade: {grade}\n{explanation}\n\nWould you like to learn about another topic? Reply 'yes' or 'no'."

    new_state: HealthBotState = {
        **state,
        "grade": "Correct" if grade.lower().startswith("c") else "Incorrect",
        "explanation": explanation,
        "status": "ask_restart",
        "bot_message": message,
    }
    # Breakpoint: wait for user to respond yes/no
    new_state["user_message"] = ""
    return new_state


def node_present_grade(state: HealthBotState) -> HealthBotState:
    # Transition to ask_restart (already done in evaluate) – keep as a no-op for clarity
    return state


def node_handle_restart(state: HealthBotState) -> HealthBotState:
    user_message = (state.get("user_message") or "").strip().lower()
    if user_message in {"yes", "y", "restart", "again"}:
        # Reset sensitive state
        return {
            "status": "collecting_topic",
            "bot_message": "Okay! What health topic or medical condition would you like to learn about?",
        }
    else:
        return {
            **state,
            "status": "ended",
            "bot_message": "Thanks for learning with HealthBot. Take care!",
        }


def router(state: HealthBotState) -> str:
    status = state.get("status", "collecting_topic")
    if status == "collecting_topic":
        return "collect_topic"
    if status == "searching":
        return "search"
    if status == "summarizing":
        return "summarize"
    if status == "presenting_summary":
        return "present_summary"
    if status == "awaiting_ready_for_quiz":
        # Continue only if user says ready
        user = (state.get("user_message") or "").strip().lower()
        return "generate_question" if user in {"ready", "r", "ok", "go"} else END
    if status == "generating_question":
        return "generate_question"
    if status == "awaiting_answer":
        # Proceed to evaluate once an answer A-D arrives
        import re
        ans = (state.get("user_message") or "").strip().upper()
        return "evaluate" if re.fullmatch(r"[ABCD]", ans) else END
    if status == "evaluating":
        return "evaluate"
    if status == "presenting_grade":
        return "present_grade"
    if status == "ask_restart":
        # Proceed once user responds yes/no
        user = (state.get("user_message") or "").strip().lower()
        return "handle_restart" if user in {"yes", "y", "no", "n", "restart", "again"} else END
    return END


def build_graph():
    graph = StateGraph(HealthBotState)

    graph.add_node("collect_topic", node_collect_topic)
    graph.add_node("search", node_search)
    graph.add_node("summarize", node_summarize)
    graph.add_node("present_summary", node_present_summary)
    graph.add_node("generate_question", node_generate_question)
    graph.add_node("evaluate", node_evaluate)
    graph.add_node("present_grade", node_present_grade)
    graph.add_node("handle_restart", node_handle_restart)

    graph.set_conditional_entry_point(router)
    graph.add_conditional_edges("collect_topic", router)
    graph.add_conditional_edges("search", router)
    graph.add_conditional_edges("summarize", router)
    graph.add_conditional_edges("present_summary", router)
    graph.add_conditional_edges("generate_question", router)
    graph.add_conditional_edges("evaluate", router)
    graph.add_conditional_edges("present_grade", router)
    graph.add_conditional_edges("handle_restart", router)

    # Use DynamoDB checkpointing with custom configuration
    table_config = DynamoDBTableConfig(
        table_name=os.environ.get('SESSION_STATE_TABLE', 'healthbot-backend-session-state-dev'),
        billing_mode="PAY_PER_REQUEST",
        enable_encryption=True,
        enable_point_in_time_recovery=True,
        ttl_days=30
    )
    
    config = DynamoDBConfig(
        table_config=table_config,
        region_name=os.environ.get('AWS_REGION', 'us-east-1')
    )
    
    # Use deploy=False since we're managing the table via CloudFormation
    checkpointer = DynamoDBSaver(config, deploy=False)
    
    return graph.compile(checkpointer=checkpointer)


# Create a module-level compiled graph for reuse across invocations
GRAPH = build_graph()


