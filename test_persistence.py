import asyncio
import os
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from app.graph.builder import build_graph

load_dotenv()

async def test_chat_persistence():
    DATABASE_URL = os.getenv("DATABASE_URL")
    
    graph = build_graph()
    
    config = {"configurable": {"thread_id": "test_persistence_thread"}}
    state = {"messages": [HumanMessage(content="Hello, who are you?")]}
    
    print("Testing graph execution directly with AsyncPostgresSaver...")
    
    async with AsyncPostgresSaver.from_conn_string(DATABASE_URL) as checkpointer:
        await checkpointer.setup()
        
        runnable = build_graph(checkpointer=checkpointer)
        
        # Run standard invoke to ensure checkpoint is synchronous saved
        print("Invoking graph...")
        result = await runnable.ainvoke(state, config=config)
        print("Graph finished.")
        
        # Verify checkpoint exists
        saved_state = await checkpointer.aget_tuple(config)
        if saved_state and saved_state.checkpoint:
            print("SUCCESS! Checkpoint found in DB for thread 'test_persistence_thread'.")
        else:
            print("FAILURE! No checkpoint was saved to the DB.")

if __name__ == "__main__":
    if os.name == 'nt':
        # Required for Windows + psycopg async
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(test_chat_persistence())
