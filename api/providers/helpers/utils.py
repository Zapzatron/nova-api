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

AZURE_API = '2023-08-01-preview'

async def random_secret_for(name: str) -> str:
    return await providerkeys.manager.get_key(name)

async def azure_chat_completion(endpoint: str, provider: str, payload: dict) -> dict:
    key = await random_secret_for(provider)
    model = payload['model']
    deployment = model.replace('.', '').replace('-azure', '')

    return {
        'method': 'POST',
        'url': f'{endpoint}/openai/deployments/{deployment}/chat/completions?api-version={AZURE_API}',
        'payload': payload,
        'headers': {
            'api-key': key
        },
        'provider_auth': f'{provider}>{key}'
    }
