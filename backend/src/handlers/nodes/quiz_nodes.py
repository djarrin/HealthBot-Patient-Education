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
        ("system", "You are a medical educator. Generate multiple-choice questions in valid JSON format only. Do not include markdown formatting, code blocks, or any text outside the JSON."),
        ("human", (
            "Based on the following educational summary about '{topic}', create ONE multiple-choice question with 4 choices (A-D) and mark the correct answer.\n"
            "The question should test understanding of key concepts from the summary.\n"
            "Return ONLY valid JSON with this exact structure:\n"
            "{{\n"
            '  "question": "Your question text here",\n'
            '  "choices": ["Choice A text", "Choice B text", "Choice C text", "Choice D text"],\n'
            '  "correct_letter": "A"\n'
            "}}\n"
            "Make sure the question is clear and the choices are plausible but only one is correct.\n"
            "Do not include any text before or after the JSON.\n\n"
            "Summary:\n{summary}"
        ))
    ])
    
    try:
        response = llm.invoke(prompt.format_messages(summary=summary, topic=topic))
        raw = response.content
        print(f"🔍 LLM response length: {len(raw)}")
        print(f"🔍 LLM response: {raw}")
    except Exception as e:
        print(f"Error calling LLM in generate_question: {e}")
        raw = '{"question": "What is one key point from the summary?", "choices": ["A short statement that aligns with the summary", "An unrelated claim", "A contradictory claim", "An extreme or unsafe recommendation"], "correct_letter": "A"}'
    
    # Parse the JSON response
    try:
        if not raw or not raw.strip():
            raise ValueError("Empty response from LLM")
        
        # The LLM should return clean JSON, but let's validate and clean if needed
        cleaned_raw = raw.strip()
        
        # Remove markdown code blocks if present (fallback)
        if cleaned_raw.startswith("```json"):
            cleaned_raw = cleaned_raw[7:]
        if cleaned_raw.endswith("```"):
            cleaned_raw = cleaned_raw[:-3]
        cleaned_raw = cleaned_raw.strip()
        
        print(f"🔍 JSON to parse: {cleaned_raw}")
        parsed = json.loads(cleaned_raw)
        
        # Validate the parsed JSON structure
        if not isinstance(parsed, dict):
            raise ValueError("Response is not a JSON object")
        
        question_text = parsed.get("question", "")
        choices = parsed.get("choices", [])
        correct_letter = (parsed.get("correct_letter", "").strip() or "A").upper()
        
        # Validate the response structure
        if not question_text:
            raise ValueError("Missing question text")
        if not isinstance(choices, list) or len(choices) != 4:
            raise ValueError(f"Invalid choices format: expected list of 4 strings, got {type(choices)} with length {len(choices) if isinstance(choices, list) else 'N/A'}")
        if correct_letter not in ["A", "B", "C", "D"]:
            raise ValueError(f"Invalid correct_letter: expected A, B, C, or D, got {correct_letter}")
        
        # Validate that all choices are strings
        for i, choice in enumerate(choices):
            if not isinstance(choice, str):
                raise ValueError(f"Choice {i} is not a string: {type(choice)}")
            
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
    
    # Return the question directly and end execution
    print("❓ Question generated successfully, ending execution")
    return {
        **state,
        "question": formatted_question,
        "correct_answer": correct_answer,
        "multiple_choice": multiple_choice,
        "status": "awaiting_answer",
        "bot_message": "Here's a quick comprehension check:\n\n" + formatted_question,
        "response_type": "multiple_choice"
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
        print("❓ User provided answer, maintaining present_question status")
        return {
            **state,
            "status": "present_question"
        }
    
    # First time presenting question - create AI message with the question
    print("❓ First time presenting question")
    ai_message = AIMessage(
        content="Here's a quick comprehension check:\n\n" + question,
        name="healthbot",
        id=str(uuid.uuid4())
    )
    messages.append(ai_message)
    
    print("❓ Setting status to 'awaiting_answer' and ending execution")
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
        message = f"✅ Correct! {explanation}\n\nWould you like to learn about another health topic?"
    else:
        message = f"❌ Incorrect. {explanation}\n\nWould you like to learn about another health topic?"
    
    # Create AI message with evaluation
    ai_message = AIMessage(
        content=message,
        name="healthbot",
        id=str(uuid.uuid4())
    )
    messages.append(ai_message)
    
    # Return the evaluation and end execution
    print("📊 Evaluation completed, ending execution")
    return {
        **state,
        "user_answer": user_message,
        "grade": grade,
        "explanation": explanation,
        "status": "ask_restart",
        "bot_message": message,
        "response_type": "confirmation",
        "confirmation_prompt": True
    }
