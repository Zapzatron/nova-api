from .helpers import utils

ORGANIC = False # If all OpenAI endpoints should be used for the provider. If false, only a chat completions are used for this provider.
ENDPOINT = 'https://nova-00003.openai.azure.com' # (Important: read below) The endpoint for the provider. 
#! IMPORTANT: If this is an ORGANIC provider, this should be the endpoint for the API with anything BEFORE the "/v1".
MODELS = [
    'gpt-3.5-turbo',
    # 'gpt-3.5-turbo-16k',
    # 'gpt-3.5-turbo-instruct'
    # 'gpt-4',
    # 'gpt-4-32k'
]

async def chat_completion(**payload):
    return await utils.azure_chat_completion(ENDPOINT, 'azure-nva1', payload)
