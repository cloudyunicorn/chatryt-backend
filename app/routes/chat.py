from fastapi import APIRouter
from app.schemas.chat import ChatRequest
from app.graph.builder import build_graph

router = APIRouter(prefix="/chat", tags=["chat"])

graph = build_graph()

@router.post("/")
async def chat_endpoint(data: ChatRequest):
    config = {
        "configurable": {
            "thread_id": data.session_id  # 🔑 key for memory
        }
    }

    state = {
        "messages": [
            {"role": "user", "content": data.message}
        ]
    }

    result = await graph.ainvoke(state, config=config)

    return {
        "response": result["messages"][-1].content
    }