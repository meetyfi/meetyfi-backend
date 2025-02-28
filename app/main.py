from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.api import api_router
from app.db.mongodb import connect_to_mongo, close_mongo_connection
from app.config import get_settings
from app.middleware.logging import LoggingMiddleware
import logging
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

settings = get_settings()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="API for Meetyfi - Meeting Management System"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update this with your frontend domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom middleware
app.add_middleware(LoggingMiddleware)

@app.on_event("startup")
async def startup_db_client():
    await connect_to_mongo()
    logging.info("Connected to MongoDB")

@app.on_event("shutdown")
async def shutdown_db_client():
    await close_mongo_connection()
    logging.info("Disconnected from MongoDB")

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

app.include_router(api_router, prefix="/api/v1")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)