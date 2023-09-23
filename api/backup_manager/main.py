import os
import json
import asyncio

from sys import argv
from bson import json_util
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()

MONGO_URI = os.environ['MONGO_URI']
FILE_DIR = os.path.dirname(os.path.realpath(__file__))

async def main(output_dir: str):
    await make_backup(output_dir)

async def make_backup(output_dir: str):
    output_dir = os.path.join(FILE_DIR, '..', 'backups', output_dir)

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    client = AsyncIOMotorClient(MONGO_URI)
    databases = await client.list_database_names()
    databases = {db: await client[db].list_collection_names() for db in databases}

    for database in databases:
        if database == 'local':
            continue

        if not os.path.exists(f'{output_dir}/{database}'):
            os.mkdir(f'{output_dir}/{database}')

        for collection in databases[database]:
            print(f'Initiated database backup for {database}/{collection}')
            await make_backup_for_collection(database, collection, output_dir)

async def make_backup_for_collection(database, collection, output_dir):
    path = f'{output_dir}/{database}/{collection}.json'

    client = AsyncIOMotorClient(MONGO_URI)
    collection = client[database][collection]
    documents = await collection.find({}).to_list(length=None)

    with open(path, 'w') as f:
        json.dump(documents, f, default=json_util.default)

if __name__ == '__main__':
    if len(argv) < 2 or len(argv) > 2:
        print('Usage: python3 main.py <output_dir>')
        exit(1)

    output_dir = argv[1]
    asyncio.run(main(output_dir))
