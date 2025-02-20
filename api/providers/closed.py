from .helpers import utils

ORGANIC = True
ENDPOINT = 'https://api.openai.com'
MODELS = utils.GPT_3

async def get_key() -> str:
    return await utils.random_secret_for('closed')

async def chat_completion(**kwargs):
    payload = kwargs
    key = await get_key()

    return {
        'method': 'POST',
        'url': f'{ENDPOINT}/v1/chat/completions',
        'payload': payload,
        'headers': {
            'Authorization': f'Bearer {key}'
        },
        'provider_auth': f'closed>{key}'
    }

async def organify(request: dict) -> dict:
    key = await get_key()

    request['url'] = ENDPOINT + request['path']
    request['headers']['Authorization'] = f'Bearer {key}'
    request['provider_auth'] = f'closed>{key}'

    return request
