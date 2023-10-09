import os
import sys
import aiohttp
import asyncio
import importlib
import aiofiles.os

from rich import print

def remove_duplicate_keys(file):
    with open(file, 'r', encoding='utf8') as f:
        unique_lines = set(f)

    with open(file, 'w', encoding='utf8') as f:
        f.writelines(unique_lines)

async def main():
    try:
        provider_name = sys.argv[1]

    except IndexError:
        print('List of available providers:')

        for file_name in await aiofiles.os.listdir(os.path.dirname(__file__)):
            if file_name.endswith('.py') and not file_name.startswith('_'):
                print(file_name.split('.')[0])

        sys.exit(0)

    try:
        provider = importlib.import_module(f'.{provider_name}', 'providers')
    except ModuleNotFoundError as exc:
        print(exc)
        sys.exit(1)

    if len(sys.argv) > 2:
        model = sys.argv[2] # choose a specific model
    else:
        model = provider.MODELS[-1] # choose best model

    print(f'{provider_name} @ {model}')
    req = await provider.chat_completion(model=model, messages=[{'role': 'user', 'content': '1+1='}])
    print(req)

    # launch aiohttp
    async with aiohttp.ClientSession() as session:
        async with session.request(
            method=req['method'],
            url=req['url'],
            headers=req['headers'],
            json=req['payload'],
        ) as response:
            res_json = await response.json()
            print(response.status, res_json)

asyncio.run(main())
