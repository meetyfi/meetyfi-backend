from motor.motor_asyncio import AsyncIOMotorClient
from ..config import get_settings

settings = get_settings()

class MongoDB:
    client: AsyncIOMotorClient = None

db = MongoDB()

async def get_database():
    return db.client.meetyfi

async def connect_to_mongo():
    db.client = AsyncIOMotorClient(settings.MONGODB_URL)

async def close_mongo_connection():
    db.client.close()