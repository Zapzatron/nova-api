import os
import time
import asyncio

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

try:
    from helpers import network
except ImportError:
    pass

load_dotenv()

## MONGODB Setup

conn = AsyncIOMotorClient(os.environ['MONGO_URI'])

async def _get_collection(collection_name: str):
    return conn[os.getenv('MONGO_NAME', 'nova-test')][collection_name]

async def replacer(text: str, dict_: dict) -> str:
    # This seems to exist for a very specific and dumb purpose :D
    for k, v in dict_.items():
        text = text.replace(k, v)
    return text

async def log_api_request(user: dict, incoming_request, target_url: str):
    """Logs the API Request into the database."""
    db = await _get_collection('logs')
    payload = {}

    try:
        payload = await incoming_request.json()
    except Exception as exc:
        if 'JSONDecodeError' in str(exc):
            pass

    model = payload.get('model')
    ip_address = await network.get_ip(incoming_request)

    new_log_item = {
        'timestamp': time.time(),
        'method': incoming_request.method,
        'path': incoming_request.url.path,
        'user_id': str(user['_id']),
        'security': {
            'ip': ip_address,
        },
        'details': {
            'model': model,
            'target_url': target_url
        }
    }

    inserted = await db.insert_one(new_log_item)
    log_item = await db.find_one({'_id': inserted.inserted_id})
    return log_item

async def by_id(log_id: str):
    db = await _get_collection('logs')
    return await db.find_one({'_id': log_id})

async def by_user_id(user_id: str):
    db = await _get_collection('logs')
    return await db.find({'user_id': user_id})

async def delete_by_id(log_id: str):
    db = await _get_collection('logs')
    return await db.delete_one({'_id': log_id})

async def delete_by_user_id(user_id: str):
    db = await _get_collection('logs')
    return await db.delete_many({'user_id': user_id})

async def get_logs_time_range(start: int, end: int):
    db = await _get_collection('logs')

    entries = []
    async for entry in db.find({'timestamp': {'$gte': start, '$lte': end}}):
        entries.append(entry)

    return entries

async def main():
    # how many requests in last 24 hours?
    last_24_hours = time.time() - 86400
    logs = await get_logs_time_range(last_24_hours, time.time())

    print(f'Number of logs in last 24 hours: {len(logs)}')

if __name__ == '__main__':
    asyncio.run(main())
