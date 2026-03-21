from langgraph.graph import StateGraph, START, END
from app.graph.state import ChatState
from app.graph.nodes import chatbot_node
from langgraph.checkpoint.memory import InMemorySaver

def build_graph():
    graph = StateGraph(ChatState)

    graph.add_node("chatbot", chatbot_node)

    graph.add_edge(START, "chatbot")
    graph.add_edge("chatbot", END)

    checkpointer = InMemorySaver()

    return graph.compile(checkpointer=checkpointer)