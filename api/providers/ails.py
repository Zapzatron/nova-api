from .helpers import utils

ORGANIC = False
MODELS = [
    'gpt-3.5-turbo',
    'gpt-3.5-turbo-0301',
    'gpt-3.5-turbo-16k-0613'
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
