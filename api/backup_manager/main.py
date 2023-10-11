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

async def main(output_dir: str) -> None:
    await make_backup(output_dir)

async def make_backup(output_dir: str) -> None:
    """Makes a backup of all collections in the database."""
    output_dir = os.path.join(FILE_DIR, '..', 'backups', output_dir)

    os.makedirs(output_dir, exist_ok=True)

    client = AsyncIOMotorClient(MONGO_URI)
    databases = await client.list_database_names()
    databases = {db: await client[db].list_collection_names() for db in databases}

    for database in databases:
        if database == 'local':
            continue

        os.makedirs(os.path.join(output_dir, database), exist_ok=True)

        for collection in databases[database]:
            print(f'Initiated backup for {database}/{collection}')
            await make_backup_for_collection(database, collection, output_dir)
            print(f'Finished backup for {database}/{collection}')

async def make_backup_for_collection(database, collection, output_dir) -> None:
    """Makes a backup of a collection in the database."""
    path = os.path.join(output_dir, database, f'{collection}.json')

    client = AsyncIOMotorClient(MONGO_URI)
    collection = client[database][collection]
    documents = await collection.find({}).to_list(length=None)

    with open(path, 'w') as f:
        for chunk in json.JSONEncoder(default=json_util.default).iterencode(documents):
            f.write(chunk)

if __name__ == '__main__':
    if len(argv) < 2 or len(argv) > 2:
        print('Usage: python3 main.py <output_dir>')
        exit(1)

    output_dir = argv[1]
    asyncio.run(main(output_dir))
