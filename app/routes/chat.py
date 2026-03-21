import json
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
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

    async def event_generator():
        async for event in graph.astream_events(state, config=config, version="v2"):
            kind = event["event"]
            if kind == "on_chat_model_stream":
                chunk = event["data"]["chunk"]
                if chunk.content:
                    yield f"data: {json.dumps({'content': chunk.content})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")