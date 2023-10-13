import os
import time
import random
import asyncio

from dotenv import load_dotenv
from cachetools import TTLCache
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()

cache = TTLCache(maxsize=100, ttl=10)

class KeyManager:
    def __init__(self):
        self.conn = AsyncIOMotorClient(os.environ['MONGO_URI'])

    async def _get_collection(self, collection_name: str):
        return self.conn['nova-core'][collection_name]

    async def add_key(self, provider: str, key: str, source: str='?'):
        """Adds a key to the database."""

        db = await self._get_collection('providerkeys')
        await db.insert_one({
            'provider': provider,
            'key': key,
            'rate_limited_since': None,
            'inactive_reason': None,
            'source': source,
        })

    async def get_possible_keys(self, provider: str):
        """Returns a list of possible keys for a provider."""

        db = await self._get_collection('providerkeys')
        keys = await db.find({
            'provider': provider,
            'inactive_reason': None,
            '$or': [
                {'rate_limited_until': None},
                {'rate_limited_until': {'$lte': time.time()}}
            ]
        }).to_list(length=None)

        return keys

    async def get_key(self, provider: str):
        """Returns a random key for a provider."""

        keys = await self.get_possible_keys(provider)

        if not keys:
            return '--NO_KEY--'

        key = random.choice(keys)
        api_key = key['key']
        return api_key

    async def rate_limit_key(self, provider: str, key: str, duration: int):
        """Rate limits a key for a provider."""

        db = await self._get_collection('providerkeys')
        await db.update_one({'provider': provider, 'key': key}, {
            '$set': {
                'rate_limited_until': time.time() + duration
            }
        })

    async def deactivate_key(self, provider: str, key: str, reason: str):
        """Deactivates a key for a provider, and gives a reason."""

        db = await self._get_collection('providerkeys')
        await db.update_one({'provider': provider, 'key': key}, {
            '$set': {
                'inactive_reason': reason
            }
        })

    async def import_all(self):
        """Imports all keys from the secret/ folder."""

        db = await self._get_collection('providerkeys')
        num = 0

        for filename in os.listdir(os.path.join('api', 'secret')):
            if filename.endswith('.txt'):
                with open(os.path.join('api', 'secret', filename)) as f:
                    async for line in f:
                        if not line.strip():
                            continue

                        await db.insert_one({
                            'provider': filename.split('.')[0],
                            'key': line.strip(),
                            'source': 'import'
                        })
                        num += 1

                    print(f'[+] Imported {num} keys')

        print('[+] Done importing keys!')

    async def delete_empty_keys(self):
        db = await self._get_collection('providerkeys')
        await db.delete_many({'key': ''})

manager = KeyManager()

async def main():
    keys = await manager.get_possible_keys('closed')
    print(keys)

if __name__ == '__main__':
    asyncio.run(main())
