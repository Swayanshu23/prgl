"""
MongoDB connection via Motor (async).
Collections:
  - audit_log      : every /verify call is recorded here
  - webhook_config : registered webhook URLs
  - bulk_jobs      : bulk CSV verification jobs

MongoDB is OPTIONAL — the core pipeline runs without it.
If MongoDB is unavailable, audit logging and admin routes return empty data.
"""
from __future__ import annotations
import os
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
MONGO_DB  = os.getenv("MONGO_DB",  "prgi")

# Module-level singletons
_client: AsyncIOMotorClient | None = None
_db:     AsyncIOMotorDatabase | None = None
MONGO_AVAILABLE: bool = False          # set to True only after successful ping


def get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(
            MONGO_URL,
            serverSelectionTimeoutMS=2000,
            connectTimeoutMS=2000,
            socketTimeoutMS=2000,
        )
    return _client


def get_db() -> AsyncIOMotorDatabase | None:
    """Return DB handle, or None if MongoDB is unavailable."""
    if not MONGO_AVAILABLE:
        return None
    global _db
    if _db is None:
        _db = get_client()[MONGO_DB]
    return _db


async def init_db() -> None:
    """Attempt to connect and create indexes. Sets MONGO_AVAILABLE flag."""
    global MONGO_AVAILABLE, _db
    try:
        client = get_client()
        # Ping to verify the connection is actually up
        await client.admin.command("ping")
        _db = client[MONGO_DB]
        await _db.audit_log.create_index("created_at")
        await _db.audit_log.create_index("title")
        await _db.audit_log.create_index("verdict")
        await _db.webhook_config.create_index("url", unique=True)
        MONGO_AVAILABLE = True
        print(f"[INFO] MongoDB connected → {MONGO_URL}/{MONGO_DB}")
    except Exception as e:
        MONGO_AVAILABLE = False
        print(f"[WARN] MongoDB unavailable ({e.__class__.__name__}) — audit logging disabled")
        print(f"[WARN] Start MongoDB to enable: mongod --dbpath /data/db")


async def close_db() -> None:
    global _client, _db, MONGO_AVAILABLE
    if _client:
        _client.close()
        _client = None
        _db = None
    MONGO_AVAILABLE = False
