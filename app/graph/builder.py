import os
from langgraph.graph import StateGraph, START, END
from app.graph.state import ChatState
from app.graph.nodes import chatbot_node
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import AsyncConnectionPool

DATABASE_URL = os.getenv("DATABASE_URL")

# Make this a singleton pool or manage it correctly in FastAPI
# For this example, we'll create the pool globally or locally
connection_kwargs = {
    "autocommit": True,
    "prepare_threshold": 0,
}

# We'll need to instantiate this asynchronously or pass a connection
# to avoid blocking calls in astream_events

def build_graph(checkpointer=None):
    graph = StateGraph(ChatState)

    graph.add_node("chatbot", chatbot_node)

    graph.add_edge(START, "chatbot")
    graph.add_edge("chatbot", END)
    
    # We compile the graph with the checkpointer if provided
    return graph.compile(checkpointer=checkpointer)