from .helpers import utils

ORGANIC = False
MODELS = [
    'gpt-3.5-turbo',
    'gpt-3.5-turbo-0613',
    'gpt-4',
    'gpt-3.5-turbo-16k',
    'gpt-4-0613'
]

async def chat_completion(**kwargs):
    payload = kwargs
    key = await utils.random_secret_for('ai.ls')

    return {
        'method': 'POST',
        'url': 'https://api.caipacity.com/v1/chat/completions',
        'payload': payload,
        'headers': {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {key}'
        },
        'provider_auth': f'ai.ls>{key}'
    }
