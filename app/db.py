import os
from pymongo import MongoClient
from dotenv import load_dotenv
from app.config import MONGO_URI
from app.config import MONGO_DB_NAME

# load_dotenv()

client = MongoClient(MONGO_URI)
db = client[MONGO_DB_NAME]

print(client)

def get_database():
    return db
