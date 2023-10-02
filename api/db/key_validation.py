import os
import time
import asyncio
import json

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()

MONGO_URI = os.getenv('MONGO_URI')

async def log_rated_key(key: str) -> None:
    """Logs a key that has been rate limited to the database."""

    client = AsyncIOMotorClient(MONGO_URI)

    scheme = {
        'key': key,
        'timestamp_added': int(time.time())
    }

    collection = client['Liabilities']['rate-limited-keys']
    await collection.insert_one(scheme)


async def key_is_rated(key: str) -> bool:
    """Checks if a key is rate limited."""

    client = AsyncIOMotorClient(MONGO_URI)
    collection = client['Liabilities']['rate-limited-keys']

    query = {
        'key': key
    }

    result = await collection.find_one(query)
    return result is not None


async def cached_key_is_rated(key: str) -> bool:
    path = os.path.join(os.getcwd(), 'cache', 'rate_limited_keys.json')

    with open(path, 'r') as file:
        keys = json.load(file)

    return key in keys

async def remove_rated_keys() -> None:
    """Removes all keys that have been rate limited for more than a day."""

    a_day = 86400

    client = AsyncIOMotorClient(MONGO_URI)
    collection = client['Liabilities']['rate-limited-keys']

    keys = await collection.find().to_list(length=None)

    marked_for_removal = []
    for key in keys:
        if int(time.time()) - key['timestamp_added'] > a_day:
            marked_for_removal.append(key['_id'])

    query = {
        '_id': {
            '$in': marked_for_removal
        }
    }

    await collection.delete_many(query)

async def cache_all_keys() -> None:
    """Clones all keys from the database to the cache."""

    client = AsyncIOMotorClient(MONGO_URI)
    collection = client['Liabilities']['rate-limited-keys']

    keys = await collection.find().to_list(length=None)
    keys = [key['key'] for key in keys]

    path = os.path.join(os.getcwd(), 'cache', 'rate_limited_keys.json')
    with open(path, 'w') as file:
        json.dump(keys, file)

if __name__ == "__main__":
    asyncio.run(remove_rated_keys())
