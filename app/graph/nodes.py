from app.services.llm import llm

async def chatbot_node(state):
    response = await llm.ainvoke(state["messages"])
    
    return {
        "messages": [response]
    }