import json
from typing import List
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.schemas.chat import ChatRequest
from app.graph.builder import build_graph
from langchain_core.messages import HumanMessage, AIMessage

router = APIRouter(prefix="/chat", tags=["chat"])

# Compile the graph once
graph = build_graph()

import os
from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

DATABASE_URL = os.getenv("DATABASE_URL")
connection_kwargs = {
    "autocommit": True,
    "prepare_threshold": 0,
}

@router.post("/")
async def chat_endpoint(data: ChatRequest):
    session_id = data.session_id or "default"
    user_id = data.user_id or "default"
    
    # Use composite thread_id for LangGraph checkpointer
    composite_thread_id = f"{user_id}::{session_id}"
    
    config = {
        "configurable": {
            "thread_id": composite_thread_id
        }
    }

    state = {
        "messages": [
            HumanMessage(content=data.message)
        ]
    }

    async def event_generator():
        async with AsyncConnectionPool(conninfo=DATABASE_URL, kwargs=connection_kwargs) as pool:
            checkpointer = AsyncPostgresSaver(pool)
            await checkpointer.setup()
            
            local_graph = build_graph(checkpointer=checkpointer)
            
            async for event in local_graph.astream_events(state, config=config, version="v2"):
                kind = event["event"]
                if kind == "on_chat_model_stream":
                    chunk = event["data"]["chunk"]
                    if chunk.content:
                        yield f"data: {json.dumps({'content': chunk.content})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.get("/threads")
async def list_threads(user_id: str = "default"):
    """List threads specifically for a user_id based on composite string"""
    if not DATABASE_URL:
        raise HTTPException(status_code=500, detail="DATABASE_URL not configured")
        
    try:
        threads_data = {}
        async with AsyncConnectionPool(conninfo=DATABASE_URL, kwargs=connection_kwargs) as pool:
            checkpointer = AsyncPostgresSaver(pool)
            # Ensure tables exist before querying
            await checkpointer.setup()
            
            async for state in checkpointer.alist(None):
                raw_thread_id = state.config["configurable"].get("thread_id", "")
                
                # Check if it matches user's prefix
                prefix = f"{user_id}::"
                if raw_thread_id.startswith(prefix):
                    session_id = raw_thread_id[len(prefix):]
                    if not session_id:
                        continue
                        
                    # Get timestamp from checkpoint
                    updated_at = state.checkpoint.get("ts", "")
                    
                    # We want the latest information for each session_id
                    if session_id not in threads_data or updated_at > threads_data[session_id]["updated_at"]:
                        # Extract title from the FIRST human message if possible
                        # Checkpoints store history, so we look for the earliest human message
                        messages = state.checkpoint.get("channel_values", {}).get("messages", [])
                        if not messages and "messages" in state.checkpoint:
                             messages = state.checkpoint["messages"]
                             
                        title = "New Chat"
                        if messages:
                            # Usually the first message is the user prompt
                            for msg in messages:
                                is_human = isinstance(msg, HumanMessage) or (isinstance(msg, dict) and (msg.get("type") == "human" or msg.get("role") == "user"))
                                if is_human:
                                    content = getattr(msg, "content", "") if not isinstance(msg, dict) else msg.get("content", "")
                                    if content:
                                        title = content[:40] + ("..." if len(content) > 40 else "")
                                        break
                                        
                        threads_data[session_id] = {
                            "id": session_id,
                            "title": title,
                            "updated_at": updated_at
                        }
        
        # Sort by updated_at descending
        sorted_threads = sorted(threads_data.values(), key=lambda x: x["updated_at"], reverse=True)
        return {"threads": sorted_threads}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history/{thread_id}")
async def get_history(thread_id: str, user_id: str = "default"):
    """Get message history for a specific session mapped to a user"""
    composite_thread_id = f"{user_id}::{thread_id}"
    
    config = {
        "configurable": {
            "thread_id": composite_thread_id
        }
    }
    
    if not DATABASE_URL:
        raise HTTPException(status_code=500, detail="DATABASE_URL not configured")
        
    async with AsyncConnectionPool(conninfo=DATABASE_URL, kwargs=connection_kwargs) as pool:
        checkpointer = AsyncPostgresSaver(pool)
        await checkpointer.setup()
        saved = await checkpointer.aget_tuple(config)
        
        if not saved or not saved.checkpoint:
            return {"messages": []}
            
        messages = saved.checkpoint.get("channel_values", {}).get("messages", [])
        
        # If the state graph structure places messages directly or elsewhere:
        # We handle it defensively
        if not messages and "messages" in saved.checkpoint:
             messages = saved.checkpoint["messages"]
             
    formatted_messages = []
    for msg in messages:
        # Handle dict or HumanMessage/AIMessage objects
        if isinstance(msg, dict):
            content = msg.get("content", "")
            role = msg.get("role", msg.get("type", "user"))
            msg_id = msg.get("id", str(hash(content)))
        else:
            content = msg.content
            role = "user" if isinstance(msg, HumanMessage) else "assistant"
            msg_id = getattr(msg, "id", None) or str(hash(content))
            
        formatted_messages.append({
            "id": msg_id,
            "role": role,
            "content": content
        })
    
    return {"messages": formatted_messages}