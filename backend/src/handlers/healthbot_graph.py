import os
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolNode
from langgraph_checkpoint_dynamodb import DynamoDBSaver, DynamoDBConfig, DynamoDBTableConfig

# Import our modular components
from .types import HealthBotState
from .tools import web_search
from .routers import router, entry_router, tool_router, present_summary_router, present_question_router, generate_question_router, evaluate_router, handle_restart_router
from .nodes.topic_nodes import node_collect_topic, node_search
from .nodes.summary_nodes import node_summarize, node_present_summary
from .nodes.quiz_nodes import node_generate_question, node_present_question, node_evaluate
from .nodes.restart_nodes import node_handle_restart


def build_graph(checkpointer=None):
    """Build the HealthBot workflow graph"""
    graph = StateGraph(HealthBotState)

    # Add nodes
    graph.add_node("collect_topic", node_collect_topic)
    graph.add_node("search", node_search)
    graph.add_node("tools", ToolNode([web_search]))
    graph.add_node("summarize", node_summarize)
    graph.add_node("present_summary", node_present_summary)
    graph.add_node("generate_question", node_generate_question)
    graph.add_node("present_question", node_present_question)
    graph.add_node("evaluate", node_evaluate)
    graph.add_node("handle_restart", node_handle_restart)

    # Add conditional entry edge to route based on current status
    graph.add_conditional_edges(
        source=START,
        path=entry_router,
        path_map=["collect_topic", "present_summary", "generate_question", "present_question", "handle_restart", "evaluate", "search", "summarize"]
    )
    
    # Add sequential flow edges
    graph.add_edge("collect_topic", "search")
    graph.add_edge("search", "tools")  # Search creates tool calls, so go directly to tools
    graph.add_edge("tools", "summarize")  # Tools always go to summarize after execution
    graph.add_edge("summarize", "present_summary")
    
    # Add conditional edges for user interaction points
    graph.add_conditional_edges(
        source="present_summary",
        path=present_summary_router,
        path_map=["generate_question", "collect_topic", END]
    )
    
    graph.add_conditional_edges(
        source="generate_question",
        path=generate_question_router,
        path_map=[END]
    )
    
    graph.add_conditional_edges(
        source="present_question",
        path=present_question_router,
        path_map=["evaluate", END]
    )
    
    graph.add_conditional_edges(
        source="evaluate",
        path=evaluate_router,
        path_map=[END]
    )
    
    graph.add_conditional_edges(
        source="handle_restart",
        path=handle_restart_router,
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
        
        # Use deploy=True to let LangGraph handle table configuration
        checkpointer = DynamoDBSaver(config, deploy=True)
    
    compiled_graph = graph.compile(checkpointer=checkpointer)
    print("✅ Graph compiled successfully with checkpointer")
    return compiled_graph


# Export the build_graph function for use in other modules
__all__ = ['build_graph', 'HealthBotState']


