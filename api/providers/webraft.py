from .helpers import utils

AUTH = True
ORGANIC = False
STREAMING = True
MODELS = [
    'gpt-3.5-turbo-0613',
    'gpt-3.5-turbo-0301',
    'gpt-3.5-turbo-16k-0613'
]

async def chat_completion(**kwargs):
    payload = kwargs
    key = await utils.random_secret_for('webraft')

    return {
        'method': 'POST',
        'url': 'https://thirdparty.webraft.in/v1/chat/completions',
        'payload': payload,
        'headers': {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {key}'
        },
        'provider_auth': f'webraft>{key}'
    }
