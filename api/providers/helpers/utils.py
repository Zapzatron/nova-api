try:
    from db import providerkeys
except ModuleNotFoundError:
    from ...db import providerkeys

GPT_3 = [
    'gpt-3.5-turbo',
    'gpt-3.5-turbo-16k',
    'gpt-3.5-turbo-0613',
    'gpt-3.5-turbo-0301',
    'gpt-3.5-turbo-16k-0613',
]

GPT_4 = GPT_3 + [
    'gpt-4',
    'gpt-4-0314',
    'gpt-4-0613',
]

GPT_4_32K = GPT_4 + [
    'gpt-4-32k',
    'gpt-4-32k-0314',
    'gpt-4-32k-0613',
]

async def random_secret_for(name: str) -> str:
    return await providerkeys.manager.get_key(name)
