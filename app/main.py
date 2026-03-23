import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from app.routes import chat

# Create FastAPI app
app = FastAPI(
    title="AI Chatbot Backend",
    description="LangGraph-powered AI chatbot API",
    version="1.0.0"
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