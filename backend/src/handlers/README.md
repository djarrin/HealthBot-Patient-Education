# HealthBot Handlers - Modular Architecture

This directory contains the refactored HealthBot workflow handlers, organized into a modular structure for better maintainability and debugging.

## File Structure

```
handlers/
├── README.md                           # This file
├── healthbot_graph.py                  # Main graph builder (entry point)
├── process_user_message.py             # Lambda handler for user messages
├── response_types.py                   # Response type definitions
├── types.py                           # Type definitions and schemas
├── clients.py                         # LLM and external client setup
├── tools.py                           # LangChain tools (web search)
├── routers.py                         # Graph routing logic
└── nodes/                             # Workflow nodes organized by function
    ├── __init__.py
    ├── topic_nodes.py                 # Topic collection and search nodes
    ├── summary_nodes.py               # Summary generation and presentation
    ├── quiz_nodes.py                  # Quiz generation, presentation, and evaluation
    └── restart_nodes.py               # Session restart and cleanup
```

## Module Descriptions

### Core Files

- **`healthbot_graph.py`**: Main entry point that builds the LangGraph workflow. Imports all modular components and constructs the graph with proper routing.

- **`types.py`**: Contains all type definitions including:
  - `HealthBotState`: Main state schema for the workflow
  - `MultipleChoiceQuestion`: Quiz question structure
  - `ConfirmationPrompt`: Frontend confirmation prompts

- **`clients.py`**: External service clients:
  - `get_llm()`: OpenAI/Volcengine LLM client setup
  - `get_tavily_client()`: Tavily search client setup

- **`tools.py`**: LangChain tools:
  - `web_search()`: Medical information search tool

- **`routers.py`**: Graph routing logic:
  - `router()`: Main user interaction router
  - `entry_router()`: Entry point routing based on state
  - `tool_router()`: Tool execution routing

### Node Modules

- **`nodes/topic_nodes.py`**:
  - `node_collect_topic()`: Collects user's health topic
  - `node_search()`: Initiates web search for medical information

- **`nodes/summary_nodes.py`**:
  - `node_summarize()`: Generates patient-friendly summaries
  - `node_present_summary()`: Presents summary with quiz confirmation

- **`nodes/quiz_nodes.py`**:
  - `node_generate_question()`: Creates multiple-choice questions
  - `node_present_question()`: Presents quiz to user
  - `node_evaluate()`: Evaluates user answers and provides feedback

- **`nodes/restart_nodes.py`**:
  - `node_handle_restart()`: Handles session restart or termination

## Benefits of This Structure

1. **Modularity**: Each component has a single responsibility
2. **Maintainability**: Easier to locate and modify specific functionality
3. **Testability**: Individual components can be tested in isolation
4. **Debugging**: Clear separation makes it easier to trace issues
5. **Reusability**: Components can be reused or modified independently

## Usage

The main entry point remains the same - import `build_graph` from `healthbot_graph.py`:

```python
from handlers.healthbot_graph import build_graph

# Build the graph
graph = build_graph()

# Use the graph as before
result = graph.invoke({"user_message": "Tell me about diabetes"})
```

## Development Workflow

When adding new functionality:

1. **New types**: Add to `types.py`
2. **New clients**: Add to `clients.py`
3. **New tools**: Add to `tools.py`
4. **New nodes**: Add to appropriate `nodes/*.py` file or create new file
5. **New routers**: Add to `routers.py`
6. **Graph changes**: Update `healthbot_graph.py`

This structure makes the codebase much more manageable while preserving all existing functionality.
