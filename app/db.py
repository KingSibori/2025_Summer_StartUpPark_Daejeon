from pymongo import MongoClient
from bson import ObjectId
from .config import MONGO_URI, MONGO_DB_NAME

_client: MongoClient | None = None
_db = None


def get_client() -> MongoClient:
    global _client
    if _client is None:
        _client = MongoClient(MONGO_URI)
    return _client


def get_db():
    global _db
    if _db is None:
        _db = get_client()[MONGO_DB_NAME]
    return _db


def get_messages_collection():
    return get_db()["messages"]


def serialize_document(doc):
    """MongoDB 문서를 JSON 직렬화 가능한 형태로 변환"""
    doc["_id"] = str(doc["_id"])
    if doc is None:
        return None

    if isinstance(doc, dict):
        result = {}
        for key, value in doc.items():
            if key == "_id" and isinstance(value, ObjectId):
                result[key] = str(value)
            elif isinstance(value, ObjectId):
                result[key] = str(value)
            elif isinstance(value, dict):
                result[key] = serialize_document(value)
            elif isinstance(value, list):
                result[key] = [serialize_document(item) for item in value]
            else:
                result[key] = value
        return result
    elif isinstance(doc, list):
        return [serialize_document(item) for item in doc]
    else:
        return doc
