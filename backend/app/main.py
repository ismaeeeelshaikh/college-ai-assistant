from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
# Remove the init_db import
from .routers import auth, chat

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup - remove the init_db call
    yield
    # Shutdown
    pass

app = FastAPI(
    title="College AI Chatbot",
    description="AI-powered chatbot for college information",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(chat.router)

@app.get("/")
async def root():
    return {"message": "College AI Chatbot API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
