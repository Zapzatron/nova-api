from .helpers import utils

AUTH = True # If the provider requires an API key
ORGANIC = False # If all OpenAI endpoints are available on the provider. If false, only a chat completions are available.
STREAMING = True # If the provider supports streaming completions
ENDPOINT = 'https://nova-00001.openai.azure.com' # (Important: read below) The endpoint for the provider. 
#! IMPORTANT: If this is an ORGANIC provider, this should be the endpoint for the API with anything BEFORE the "/v1".
MODELS = [
    'gpt-3.5-turbo',
    'gpt-3.5-turbo-16k',
    'gpt-4',
    'gpt-4-32k'
]
MODELS += [f'{model}-azure' for model in MODELS]

AZURE_API = '2023-08-01-preview'

async def chat_completion(**payload):
    key = await utils.random_secret_for('azure-nva1')

    deployment = payload['model'].replace('.', '').replace('-azure', '')

    return {
        'method': 'POST',
        'url': f'{ENDPOINT}/openai/deployments/{deployment}/chat/completions?api-version={AZURE_API}',
        'payload': payload,
        'headers': {
            'api-key': key
        },
        'provider_auth': f'azure-nva1>{key}'
    }
