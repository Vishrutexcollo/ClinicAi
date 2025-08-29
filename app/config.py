# app/config.py
import os
from dotenv import load_dotenv

load_dotenv()

# Prefer Atlas if provided, else local
MONGO_URI = (
    os.getenv("MONGO_URI")
    or os.getenv("MONGODB_URI")
    or "mongodb://127.0.0.1:27017"
)
MONGO_DB_NAME = (
    os.getenv("MONGO_DB_NAME")
    or os.getenv("DB_NAME")
    or "doctorai"
)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Default collection name used across models/services
COLLECTION_NAME = os.getenv("MONGO_COLLECTION", "clinicAi")
