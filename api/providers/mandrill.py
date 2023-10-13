from .helpers import utils

ORGANIC = False
MODELS = ['llama-2-7b-chat']

async def chat_completion(**kwargs):
    payload = kwargs
    key = await utils.random_secret_for('mandrill')

    return {
        'method': 'POST',
        'url': 'https://api.mandrillai.tech/v1/chat/completions',
        'payload': payload,
        'headers': {
            'Authorization': f'Bearer {key}'
        },
        'provider_auth': f'mandrill>{key}'
    }
