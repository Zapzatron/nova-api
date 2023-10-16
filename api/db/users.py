import os
import yaml
import random
import string
import asyncio

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

try:
    from . import helpers
except ImportError:
    import helpers

load_dotenv()

with open(os.path.join(helpers.root, 'api', 'config', 'config.yml'), encoding='utf8') as f:
    credits_config = yaml.safe_load(f)

infix = os.getenv('KEYGEN_INFIX', 'S3LFH0ST')

async def generate_api_key():
    chars = string.ascii_letters + string.digits

    suffix = ''.join(random.choices(chars, k=20))
    prefix = ''.join(random.choices(chars, k=20))

    new_api_key = f'nv2-{prefix}{infix}{suffix}'
    return new_api_key

class UserManager:
    """
    Manager of all users in the database.
    """

    def __init__(self):
        self.conn = AsyncIOMotorClient(os.environ['MONGO_URI'])

    async def _get_collection(self, collection_name: str):
        return self.conn[os.getenv('MONGO_NAME', 'nova-test')][collection_name]
    
    async def get_all_users(self):
        collection = self.conn['nova-core']['users']
        return collection#.find()

    async def create(self, discord_id: str = '') -> dict:
        db = await self._get_collection('users')

        new_api_key = await generate_api_key()
        existing_user = await self.user_by_discord_id(discord_id)
        if existing_user: # just change api key
            await db.update_one({'auth.discord': str(int(discord_id))}, {'$set': {'api_key': new_api_key}})
        else:
            new_user = {
                'api_key': new_api_key,
                'credits': credits_config['start-credits'],
                'role': '',
                'level': '',
                'status': {
                    'active': True,
                    'ban_reason': '',
                },
                'auth': {
                    'discord': str(discord_id),
                    'github': None
                }
            }

            await db.insert_one(new_user)
        user = await db.find_one({'api_key': new_api_key})
        return user

    async def user_by_id(self, user_id: str):
        db = await self._get_collection('users')
        return await db.find_one({'_id': user_id})

    async def user_by_discord_id(self, discord_id: str):
        db = await self._get_collection('users')

        user = await db.find_one({'auth.discord': str(discord_id)})

        if not user:
            return

        if user['api_key'] == '':
            new_api_key = await generate_api_key()
            await db.update_one({'auth.discord': str(discord_id)}, {'$set': {'api_key': new_api_key}})
            user = await db.find_one({'auth.discord': str(discord_id)})

        return user

    async def user_by_api_key(self, key: str):
        db = await self._get_collection('users')
        return await db.find_one({'api_key': key})

    async def update_by_id(self, user_id: str, update):
        db = await self._get_collection('users')
        return await db.update_one({'_id': user_id}, update)

    async def update_by_discord_id(self, discord_id: str, update):
        db = await self._get_collection('users')

        return await db.update_one({'auth.discord': str(int(discord_id))}, update)

    async def update_by_filter(self, obj_filter, update):
        db = await self._get_collection('users')
        return await db.update_one(obj_filter, update)

    async def delete(self, user_id: str):
        db = await self._get_collection('users')
        await db.delete_one({'_id': user_id})

manager = UserManager()

async def demo():
    user = await UserManager().create('1099385227077488700')
    print(user)

if __name__ == '__main__':
    asyncio.run(demo())
