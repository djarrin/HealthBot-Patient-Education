from __future__ import annotations

import os
import json
import re
import uuid
from typing import Any, Dict, List, Literal, Optional, TypedDict, Union, Annotated

from langchain_openai import ChatOpenAI
from langchain_core.messages import (
    HumanMessage, SystemMessage, AIMessage, ToolMessage, RemoveMessage
)
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain_core.tools.base import InjectedToolCallId
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import MessagesState, add_messages
from langgraph_checkpoint_dynamodb import DynamoDBSaver, DynamoDBConfig, DynamoDBTableConfig
from langgraph.prebuilt import ToolNode
from langgraph.types import Command
from tavily import TavilyClient


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


def _get_llm() -> ChatOpenAI:
    # Debug API key loading
    api_key = os.environ.get("OPENAI_API_KEY", "")
    print(f"OpenAI API Key (first 10 chars): {api_key[:10]}...")
    print(f"OpenAI API Key length: {len(api_key)}")
    
    # For Volcengine relay, we need to configure the base URL
    # Volcengine typically uses a different endpoint
    base_url = os.environ.get("OPENAI_BASE_URL", "https://openai.vocareum.com/v1")
    print(f"Using base URL: {base_url}")
    
    # Keep a small, fast model for lambda latency
    return ChatOpenAI(
        model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"), 
        temperature=0,
        api_key=api_key,
        base_url=base_url,
        max_retries=0  # Disable retries to get immediate error feedback
    )


def _get_tavily_client() -> TavilyClient:
    """Get Tavily client for direct API access"""
    api_key = os.environ.get("TAVILY_API_KEY", "")
    if not api_key:
        raise ValueError("TAVILY_API_KEY environment variable is required")
    return TavilyClient(api_key=api_key)


@tool
def web_search(question: str) -> Dict[str, Any]:
    """
    Search for up-to-date medical information on a given health topic.
    Returns relevant, evidence-based information from trusted medical sources.
    """
    try:
        tavily_client = _get_tavily_client()
        response = tavily_client.search(
            question,
            search_depth="advanced",
            max_results=8,
            include_domains=["mayoclinic.org", "healthline.com", "webmd.com", "medlineplus.gov", "cdc.gov", "nih.gov"]
        )
        return response
    except Exception as e:
        print(f"Error in web_search: {e}")
        return {
            "results": [],
            "error": str(e)
        }


def node_collect_topic(state: HealthBotState) -> HealthBotState:
    print("📝 Node: collect_topic")
    messages = state["messages"]
    user_message = (state.get("user_message") or "").strip()
    
    # Create system message if this is the first interaction
    if not messages:
        system_prompt = (
            "You are a medical education assistant helping patients learn about health topics. "
            "Your role is to:\n"
            "1. Search for up-to-date medical information from trusted sources\n"
            "2. Create patient-friendly summaries with citations\n"
            "3. Generate comprehension questions to test understanding\n"
            "4. Provide educational feedback with explanations\n"
            "5. Guide patients through the learning process\n\n"
            "Always be accurate, educational, and encouraging. Never give medical advice."
        )
        sys_message = SystemMessage(
            content=system_prompt,
            name="system"
        )
        messages.append(sys_message)
    
    # Create human message from user input
    human_message = HumanMessage(
        content=user_message,
        name="patient",
        id=str(uuid.uuid4())
    )
    messages.append(human_message)
    
    print(f"📝 Setting status to 'searching' for topic: {user_message}")
    return {
        **state,
        "topic": user_message,
        "status": "searching",
        "bot_message": f"Got it! I'll search for trusted, up-to-date medical information on: {user_message}. This may take a moment...",
        "response_type": "text",
        "user_message": ""  # Clear consumed input
    }


def node_search(state: HealthBotState) -> HealthBotState:
    print("🔍 Node: search")
    messages = state["messages"]
    topic = state.get("topic", "").strip()
    
    # Create AI message that will call the search tool
    search_prompt = f"Search for up-to-date medical information about: {topic}"
    ai_message = AIMessage(
        content=search_prompt,
        name="healthbot",
        id=str(uuid.uuid4()),
        tool_calls=[{
            "id": str(uuid.uuid4()),
            "type": "tool_call",
            "name": "web_search",
            "args": {"question": topic}
        }]
    )
    messages.append(ai_message)
    
    print(f"🔍 Created tool call for topic: {topic}")
    return {
        **state,
        "status": "searching",  # This will trigger router to check for tool calls
        "bot_message": f"Searching for information about {topic}...",
        "response_type": "text"
    }


def node_summarize(state: HealthBotState) -> HealthBotState:
    print("📋 Node: summarize")
    messages = state["messages"]
    topic = state.get("topic", "")
    
    # Extract search results from tool messages
    search_results = []
    for message in messages:
        if isinstance(message, ToolMessage) and message.name == "web_search":
            try:
                result_data = json.loads(message.content)
                results = result_data.get("results", [])
                
                # Normalize results
                for r in results:
                    url = r.get("url") or r.get("source", "")
                    title = r.get("title") or ""
                    content = r.get("content") or r.get("snippet") or ""
                    
                    if content and len(content.strip()) > 50:
                        search_results.append({
                            "url": url,
                            "title": title,
                            "content": content
                        })
            except Exception as e:
                print(f"Error parsing search results: {e}")
    
    print(f"📋 Found {len(search_results)} search results")
    
    # If no results, provide fallback
    if not search_results:
        search_results = [{
            "url": "https://www.healthline.com",
            "title": "Health Information",
            "content": "General health information and resources. Please try rephrasing your question for more specific results."
        }]
    
    # Create summary using LLM
    llm = _get_llm()
    sources_block = "\n\n".join(
        [f"Source {i+1}: {r.get('title','').strip()} — {r.get('url','').strip()}\n{(r.get('content','') or '')[:1500]}" 
         for i, r in enumerate(search_results)]
    )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a careful medical educator. Write at a 7th–9th grade reading level. Include citations as [1], [2], etc. referencing the sources list order."),
        ("human", (
            "Summarize the most relevant, evidence-based information for a patient about the topic: '{topic}'.\n"
            "- Be accurate and neutral; avoid giving medical advice.\n"
            "- Use short paragraphs and clear language.\n"
            "- Add a 'Key Points' section at the end.\n"
            "- Include in-text citation markers like [1], [2] that map to the sources list order.\n"
            "- Keep the summary comprehensive but readable (aim for 300-500 words).\n\n"
            "Sources (ordered):\n{sources}\n"
        ))
    ])
    
    try:
        response = llm.invoke(prompt.format_messages(topic=topic, sources=sources_block))
        summary = response.content
        print("📋 Summary generated successfully")
    except Exception as e:
        print(f"Error calling LLM: {e}")
        summary = f"Unable to generate summary due to technical issues. Please try again later. Error: {str(e)}"
    
    # Build citations
    citations = [r.get("url", "") for r in search_results if r.get("url")]
    
    # Create AI message with summary
    ai_message = AIMessage(
        content=summary,
        name="healthbot",
        id=str(uuid.uuid4())
    )
    messages.append(ai_message)
    
    print("📋 Setting status to 'presenting_summary'")
    return {
        **state,
        "search_results": search_results,
        "summary": summary,
        "citations": citations,
        "status": "presenting_summary",
        "bot_message": summary,
        "response_type": "text"
    }


def node_present_summary(state: HealthBotState) -> HealthBotState:
    print("📄 Node: present_summary")
    messages = state["messages"]
    
    # Create confirmation prompt for the frontend
    confirmation_prompt: ConfirmationPrompt = {
        "message": "When you're ready for a quick comprehension check, click the button below.",
        "requires_confirmation": True
    }
    
    # Create AI message with confirmation prompt
    ai_message = AIMessage(
        content="I've provided you with comprehensive information about your health topic. When you're ready for a quick comprehension check, click the button below.",
        name="healthbot",
        id=str(uuid.uuid4())
    )
    messages.append(ai_message)
    
    print("📄 Setting status to 'presenting_summary' to pause for user interaction")
    return {
        **state, 
        "status": "presenting_summary",  # Changed from "awaiting_ready_for_quiz"
        "bot_message": "I've provided you with comprehensive information about your health topic. When you're ready for a quick comprehension check, click the button below.",
        "response_type": "confirmation",
        "confirmation_prompt": confirmation_prompt
    }


def node_generate_question(state: HealthBotState) -> HealthBotState:
    messages = state["messages"]
    summary = state.get("summary", "")
    topic = state.get("topic", "")
    
    # Create human message to trigger question generation
    human_message = HumanMessage(
        content="ready",
        name="patient",
        id=str(uuid.uuid4())
    )
    messages.append(human_message)
    
    # Generate question using LLM
    llm = _get_llm()
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Generate a single multiple-choice question that tests understanding of the medical information provided."),
        ("human", (
            "Based on the following educational summary about '{topic}', create ONE multiple-choice question with 4 choices (A-D) and mark the correct answer.\n"
            "The question should test understanding of key concepts from the summary.\n"
            "Return strict JSON with keys: question, choices (list of 4 strings), correct_letter (A-D).\n"
            "Make sure the question is clear and the choices are plausible but only one is correct.\n\n"
            "Summary:\n{summary}"
        ))
    ])
    
    try:
        response = llm.invoke(prompt.format_messages(summary=summary, topic=topic))
        raw = response.content
    except Exception as e:
        print(f"Error calling LLM in generate_question: {e}")
        raw = '{"question": "What is one key point from the summary?", "choices": ["A short statement that aligns with the summary", "An unrelated claim", "A contradictory claim", "An extreme or unsafe recommendation"], "correct_letter": "A"}'
    
    # Parse the JSON response
    try:
        parsed = json.loads(raw)
        question_text = parsed.get("question", "")
        choices = parsed.get("choices", [])
        correct_letter = (parsed.get("correct_letter", "").strip() or "A").upper()
        
        # Validate the response
        if not question_text or len(choices) != 4 or correct_letter not in ["A", "B", "C", "D"]:
            raise ValueError("Invalid question format")
            
        # Get the correct answer text
        correct_index = ["A", "B", "C", "D"].index(correct_letter)
        correct_answer = choices[correct_index]
        
        # Create the multiple choice question object
        multiple_choice: MultipleChoiceQuestion = {
            "question": question_text,
            "choices": choices,
            "correct_letter": correct_letter
        }
        
        # Format the question for display
        formatted_question = question_text + "\n\n" + "\n".join([f"{letter}. {text}" for letter, text in zip(["A","B","C","D"], choices)])
        
    except Exception as e:
        print(f"Error parsing question JSON: {e}")
        # Fallback question
        question_text = "What is one key point from the summary?"
        choices = [
            "A short statement that aligns with the summary",
            "An unrelated claim", 
            "A contradictory claim",
            "An extreme or unsafe recommendation"
        ]
        correct_answer = choices[0]
        correct_letter = "A"
        
        multiple_choice: MultipleChoiceQuestion = {
            "question": question_text,
            "choices": choices,
            "correct_letter": correct_letter
        }
        
        formatted_question = question_text + "\n\n" + "\n".join([f"{letter}. {text}" for letter, text in zip(["A","B","C","D"], choices)])
    
    # Create AI message with question
    ai_message = AIMessage(
        content="Here's a quick comprehension check:\n\n" + formatted_question,
        name="healthbot",
        id=str(uuid.uuid4())
    )
    messages.append(ai_message)
    
    return {
        **state,
        "question": formatted_question,
        "correct_answer": correct_answer,
        "multiple_choice": multiple_choice,
        "status": "awaiting_answer",
        "bot_message": "Here's a quick comprehension check:\n\n" + formatted_question,
        "response_type": "multiple_choice"
    }


def node_evaluate(state: HealthBotState) -> HealthBotState:
    messages = state["messages"]
    user_message = (state.get("user_message") or "").strip().upper()
    summary = state.get("summary", "")
    citations = state.get("citations", [])
    correct_answer = state.get("correct_answer", "")
    multiple_choice = state.get("multiple_choice", {})
    correct_letter = multiple_choice.get("correct_letter", "A")
    
    # Create human message with user's answer
    human_message = HumanMessage(
        content=user_message,
        name="patient",
        id=str(uuid.uuid4())
    )
    messages.append(human_message)
    
    # Determine if the answer is correct
    is_correct = user_message == correct_letter
    grade = "Correct" if is_correct else "Incorrect"
    
    # Create explanation with citations
    llm = _get_llm()
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a medical educator providing feedback on a student's answer. Be encouraging and educational."),
        ("human", (
            "Student selected: {user_answer}\n"
            "Correct answer: {correct_letter} ({correct_answer})\n"
            "Grade: {grade}\n\n"
            "Summary with citations:\n{summary}\n\n"
            "Provide a 2-3 sentence explanation that:\n"
            "1. Confirms if they were correct or explains why they were wrong\n"
            "2. References relevant information from the summary using citations [1], [2], etc.\n"
            "3. Reinforces the key learning points\n"
            "4. Is encouraging and educational\n\n"
            "Return only the explanation text, no JSON formatting."
        ))
    ])
    
    try:
        response = llm.invoke(
            prompt.format_messages(
                user_answer=user_message,
                correct_letter=correct_letter,
                correct_answer=correct_answer,
                grade=grade,
                summary=summary
            )
        )
        explanation = response.content
    except Exception as e:
        print(f"Error calling LLM in evaluate: {e}")
        # Fallback explanation
        if is_correct:
            explanation = f"Excellent! You selected the correct answer. The information from the summary supports this choice."
        else:
            explanation = f"Not quite right. The correct answer was {correct_letter}: {correct_answer}. Review the summary for more details."
    
    # Create the response message
    if is_correct:
        message = f"✅ Correct! {explanation}\n\nWould you like to learn about another health topic? Reply 'yes' or 'no'."
    else:
        message = f"❌ Incorrect. {explanation}\n\nWould you like to learn about another health topic? Reply 'yes' or 'no'."
    
    # Create AI message with evaluation
    ai_message = AIMessage(
        content=message,
        name="healthbot",
        id=str(uuid.uuid4())
    )
    messages.append(ai_message)
    
    return {
        **state,
        "user_answer": user_message,
        "grade": grade,
        "explanation": explanation,
        "status": "ask_restart",
        "bot_message": message,
        "response_type": "text",
        "user_message": ""  # Clear consumed input
    }


def node_handle_restart(state: HealthBotState) -> HealthBotState:
    messages = state["messages"]
    user_message = (state.get("user_message") or "").strip().lower()
    
    # Create human message with user's restart decision
    human_message = HumanMessage(
        content=user_message,
        name="patient",
        id=str(uuid.uuid4())
    )
    messages.append(human_message)
    
    if user_message in {"yes", "y", "restart", "again"}:
        # Create AI message for restart
        ai_message = AIMessage(
            content="Great! What health topic or medical condition would you like to learn about?",
            name="healthbot",
            id=str(uuid.uuid4())
        )
        messages.append(ai_message)
        
        # Reset sensitive state for privacy and accuracy
        return {
            **state,
            "status": "collecting_topic",
            "bot_message": "Great! What health topic or medical condition would you like to learn about?",
            "response_type": "text",
            # Clear all sensitive data
            "user_message": "",
            "topic": "",
            "search_results": [],
            "summary": "",
            "citations": [],
            "question": "",
            "correct_answer": "",
            "multiple_choice": None,
            "user_answer": "",
            "grade": "",
            "explanation": "",
            "confirmation_prompt": None
        }
    else:
        # Create AI message for session end
        ai_message = AIMessage(
            content="Thanks for learning with HealthBot! Take care and stay healthy! 👋",
            name="healthbot",
            id=str(uuid.uuid4())
        )
        messages.append(ai_message)
        
        return {
            **state,
            "status": "ended",
            "bot_message": "Thanks for learning with HealthBot! Take care and stay healthy! 👋",
            "response_type": "text"
        }


def router(state: HealthBotState) -> str:
    """Main router for user interaction points"""
    status = state.get("status", "collecting_topic")
    user_message = (state.get("user_message") or "").strip().lower()
    
    print(f"🔀 Router called with status: {status}, user_message: '{user_message}'")
    
    if status == "presenting_summary":
        # If user has responded, transition to generate_question
        if user_message:
            print("✅ User responded after summary, routing to generate_question")
            return "generate_question"
        else:
            # Always pause here to show summary to user
            print("⏸️  Pausing at presenting_summary to show summary to user")
            return END
    
    if status == "awaiting_ready_for_quiz":
        # Continue only if user says ready
        if user_message in {"ready", "r", "ok", "go", "yes", "y"}:
            print("✅ User ready for quiz, routing to generate_question")
            return "generate_question"
        else:
            print("❌ User not ready, ending")
            return END
    elif status == "ask_restart":
        # Proceed once user responds yes/no
        if user_message in {"yes", "y", "restart", "again"}:
            print("✅ User wants to restart, routing to collect_topic")
            return "collect_topic"
        else:
            print("❌ User wants to end, ending")
            return END
    
    print(f"⚠️  No matching status, ending")
    return END


def tool_router(state: HealthBotState) -> str:
    """Router specifically for handling tool execution flow"""
    messages = state.get("messages", [])
    
    print(f"🔧 Tool router called with {len(messages)} messages")
    
    # Check if the last message has tool calls that need to be executed
    if messages and hasattr(messages[-1], 'tool_calls') and messages[-1].tool_calls:
        print("🔧 Found tool calls, routing to tools")
        return "tools"  # Execute the tool
    
    # If no tool calls, proceed directly to summarize
    print("📝 No tool calls found, proceeding to summarize")
    return "summarize"


def build_graph(checkpointer=None):
    graph = StateGraph(HealthBotState)

    # Add nodes
    graph.add_node("collect_topic", node_collect_topic)
    graph.add_node("search", node_search)
    graph.add_node("tools", ToolNode([web_search]))
    graph.add_node("summarize", node_summarize)
    graph.add_node("present_summary", node_present_summary)
    graph.add_node("generate_question", node_generate_question)
    graph.add_node("evaluate", node_evaluate)
    graph.add_node("handle_restart", node_handle_restart)

    # Add sequential flow edges
    graph.add_edge(START, "collect_topic")
    graph.add_edge("collect_topic", "search")
    graph.add_edge("tools", "summarize")  # Tools always go to summarize after execution
    graph.add_edge("summarize", "present_summary")
    graph.add_edge("generate_question", "evaluate")
    graph.add_edge("evaluate", "handle_restart")
    
    # Add conditional edge for search to determine if tools are needed
    graph.add_conditional_edges(
        source="search",
        path=tool_router,
        path_map=["tools", "summarize"]
    )
    
    # Add conditional edges for user interaction points
    graph.add_conditional_edges(
        source="present_summary",
        path=router,
        path_map=["generate_question", END]
    )
    
    graph.add_conditional_edges(
        source="handle_restart",
        path=router,
        path_map=["collect_topic", END]
    )

    # Use provided checkpointer or default to DynamoDB
    if checkpointer is None:
        # Use DynamoDB checkpointing with custom configuration
        table_config = DynamoDBTableConfig(
            table_name=os.environ.get('SESSION_STATE_TABLE', 'healthbot-backend-session-state-v2-dev'),
            billing_mode="PAY_PER_REQUEST",
            enable_encryption=True,
            enable_point_in_time_recovery=True,
            ttl_days=None  # Disable TTL in langgraph since we handle it manually
        )
        
        config = DynamoDBConfig(
            table_config=table_config,
            region_name=os.environ.get('AWS_REGION', 'us-east-1')
        )
        
        # Use deploy=False since we're managing the table via CloudFormation
        checkpointer = DynamoDBSaver(config, deploy=False)
    
    return graph.compile(checkpointer=checkpointer)


# Note: Removed module-level GRAPH creation to avoid DynamoDB errors on import
# The graph should be created explicitly when needed using build_graph()


