import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from psycopg_pool import AsyncConnectionPool

# Load environment variables
load_dotenv()

from app.routes import chat

DATABASE_URL = os.getenv("DATABASE_URL")
connection_kwargs = {
    "autocommit": True,
    "prepare_threshold": 0,
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize connection pool
    if DATABASE_URL:
        # Create a global pool that will be reused across requests
        # Pass connection_kwargs via the explicit 'kwargs' parameter as required by psycopg_pool
        app.state.pool = AsyncConnectionPool(conninfo=DATABASE_URL, kwargs=connection_kwargs)
        
        # Initialize database tables once on startup
        try:
            from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
            checkpointer = AsyncPostgresSaver(app.state.pool)
            await checkpointer.setup()
            print("Database checkpointer initialized successfully.")
        except Exception as e:
            print(f"CRITICAL: Failed to initialize database checkpointer: {e}")
    else:
        app.state.pool = None
        print("CRITICAL: DATABASE_URL not set in environment!")
    
    yield
    
    # Close connection pool on shutdown
    if app.state.pool:
        await app.state.pool.close()

# Create FastAPI app
app = FastAPI(
    title="AI Chatbot Backend",
    description="LangGraph-powered AI chatbot API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS (important for Next.js frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:8000", "https://chatryt-green.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(chat.router)


# Health check route
@app.get("/")
async def root():
    return {"status": "ok", "message": "AI Chatbot Backend Running 🚀"}


# Optional: readiness check (useful for deployment)
@app.get("/health")
async def health():
    return {"status": "healthy"}