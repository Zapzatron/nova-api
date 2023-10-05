import os
import time
import asyncio

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()

class KeyManager:
    def __init__(self):
        self.conn = AsyncIOMotorClient(os.environ['MONGO_URI'])

    async def _get_collection(self, collection_name: str):
        return self.conn['nova-core'][collection_name]

    async def add_key(self, provider: str, key: str, source: str='?'):
        db = await self._get_collection('providerkeys')
        await db.insert_one({
            'provider': provider,
            'key': key,
            'rate_limited_since': None,
            'inactive_reason': None,
            'source': source,
        })

    async def get_key(self, provider: str):
        db = await self._get_collection('providerkeys')
        key = await db.find_one({
            'provider': provider,
            'inactive_reason': None,
            '$or': [
                {'rate_limited_since': None},
                {'rate_limited_since': {'$lte': time.time() - 86400}}
            ]
        })

        if key is None:
            return '--NO_KEY--'

        return key['key']

    async def rate_limit_key(self, provider: str, key: str):
        db = await self._get_collection('providerkeys')
        await db.update_one({'provider': provider, 'key': key}, {
            '$set': {
                'rate_limited_since': time.time()
            }
        })

    async def deactivate_key(self, provider: str, key: str, reason: str):
        db = await self._get_collection('providerkeys')
        await db.update_one({'provider': provider, 'key': key}, {
            '$set': {
                'inactive_reason': reason
            }
        })

    async def import_all(self):
        db = await self._get_collection('providerkeys')
        num = 0

        for filename in os.listdir('api/secret'):
            if filename.endswith('.txt'):
                with open(f'api/secret/{filename}') as f:
                    for line in f.readlines():
                        if not line.strip():
                            continue

                        await db.insert_one({
                            'provider': filename.split('.')[0],
                            'key': line.strip(),
                            'rate_limited_since': None,
                            'inactive_reason': None,
                            'source': 'import'
                        })
                        num += 1

                    print(f'[+] Imported {num} keys')

        print('[+] Done importing keys!')

    async def delete_empty_keys(self):
        db = await self._get_collection('providerkeys')
        await db.delete_many({'key': ''})

manager = KeyManager()

if __name__ == '__main__':
    asyncio.run(manager.import_all())
