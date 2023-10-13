import os
import asyncio

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()

class AzureManager:
    def __init__(self):
        self.conn = AsyncIOMotorClient(os.environ['MONGO_URI'])

    async def _get_collection(self, collection_name: str):
        azure_db = conn[os.getenv('MONGO_NAME', 'nova-test')][collection_name]

manager = AzureManager()

if __name__ == '__main__':
    print(asyncio.run(manager.get_entire_financial_history()))
