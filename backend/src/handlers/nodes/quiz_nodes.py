import json
import uuid
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from ..types import HealthBotState, MultipleChoiceQuestion
from ..clients import get_llm


def node_generate_question(state: HealthBotState) -> HealthBotState:
    print("❓ Node: generate_question")
    messages = state["messages"]
    summary = state.get("summary", "")
    topic = state.get("topic", "")
    user_message = (state.get("user_message") or "").strip()
    
    # Check if we already have a question (continuing from previous state)
    existing_question = state.get("question", "")
    if existing_question:
        print("❓ Continuing with existing question")
        return {
            **state,
            "status": "present_question",
            "user_message": ""  # Clear consumed input
        }
    
    # Create human message with user's confirmation
    human_message = HumanMessage(
        content=user_message or "ready",
        name="patient",
        id=str(uuid.uuid4())
    )
    messages.append(human_message)
    
    # Generate question using LLM
    llm = get_llm()
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
        print(f"🔍 LLM response: {raw[:200]}...")
    except Exception as e:
        print(f"Error calling LLM in generate_question: {e}")
        raw = '{"question": "What is one key point from the summary?", "choices": ["A short statement that aligns with the summary", "An unrelated claim", "A contradictory claim", "An extreme or unsafe recommendation"], "correct_letter": "A"}'
    
    # Parse the JSON response
    try:
        if not raw or not raw.strip():
            raise ValueError("Empty response from LLM")
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
    
    return {
        **state,
        "question": formatted_question,
        "correct_answer": correct_answer,
        "multiple_choice": multiple_choice,
        "status": "present_question",
        "user_message": ""  # Clear consumed input after generating question
    }


def node_present_question(state: HealthBotState) -> HealthBotState:
    """Present the generated question to the user and wait for their answer"""
    print("❓ Node: present_question")
    messages = state["messages"]
    question = state.get("question", "")
    multiple_choice = state.get("multiple_choice", {})
    user_message = (state.get("user_message") or "").strip()
    
    # Check if we have a user message (continuing from previous state)
    if user_message:
        print(f"❓ Processing user answer: '{user_message}'")
        # Create human message with user's answer
        human_message = HumanMessage(
            content=user_message,
            name="patient",
            id=str(uuid.uuid4())
        )
        messages.append(human_message)
        
        # Node just processes the input - router will handle routing
        print("❓ User provided answer, clearing user_message and maintaining present_question status")
        return {
            **state,
            "user_message": ""  # Clear consumed input
        }
    
    # Original logic for first time presenting question
    # Create AI message with the question
    ai_message = AIMessage(
        content="Here's a quick comprehension check:\n\n" + question,
        name="healthbot",
        id=str(uuid.uuid4())
    )
    messages.append(ai_message)
    
    print("❓ Setting status to 'awaiting_answer' to wait for user response")
    return {
        **state,
        "status": "awaiting_answer",
        "bot_message": "Here's a quick comprehension check:\n\n" + question,
        "response_type": "multiple_choice"
    }


def node_evaluate(state: HealthBotState) -> HealthBotState:
    print("📊 Node: evaluate")
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
    llm = get_llm()
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
