# app/db.py
import os
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
from app.config import MONGO_URI, MONGO_DB_NAME

USE_MOCK = os.getenv("MONGO_MOCK") == "1"

def get_mongo_client():
    """
    Returns a live, ping-tested MongoClient.
    If MONGO_MOCK=1 is set, returns an in-memory mongomock client.
    """
    if USE_MOCK:
        import mongomock  # type: ignore
        return mongomock.MongoClient()

    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")
        return client
    except ServerSelectionTimeoutError as e:
        raise RuntimeError(f"Cannot connect to MongoDB at {MONGO_URI}: {e}") from e

def get_database():
    client = get_mongo_client()
    name = MONGO_DB_NAME or "doctorai"
    return client[name]
