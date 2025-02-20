"""Does quite a few checks and prepares the incoming request for the target endpoint, so it can be streamed"""

import os
import json
import yaml
import time
import fastapi

from dotenv import load_dotenv

import responder
import moderation

from rich import print
from db.users import UserManager
from helpers import tokens, errors, network

load_dotenv()

users = UserManager()
with open(os.path.join('cache', 'models.json'), encoding='utf8') as f:
    models_list = json.load(f)
models = [model['id'] for model in models_list['data']]

moderation_debug_key = os.getenv('MODERATION_DEBUG_KEY')

async def handle(incoming_request: fastapi.Request):
    """Transfer a streaming response 
    Takes the request from the incoming request to the target endpoint.
    Checks method, token amount, auth and cost along with if request is NSFW.
    """

    path = incoming_request.url.path
    path = path.replace('/v1/v1', '/v1')

    ip_address = network.get_ip(incoming_request)

    if '/dashboard' in path:
        return await errors.error(404, 'You can\'t access /dashboard.', 'This is a private endpoint.')

    if path.startswith('/v1/models'):
        return fastapi.responses.JSONResponse(content=models_list)

    try:
        payload = await incoming_request.json()
    except json.decoder.JSONDecodeError:
        payload = {}
    except UnicodeDecodeError:
        payload = {}

    received_key = incoming_request.headers.get('Authorization')

    if not received_key or not received_key.startswith('Bearer '):
        return await errors.error(401, 'No NovaAI API key given!', 'Add \'Authorization: Bearer nv-...\' to your request headers.')

    key_tags = ''

    if '#' in received_key:
        key_tags = received_key.split('#')[1]
        received_key = received_key.split('#')[0]

    user = await users.user_by_api_key(received_key.split('Bearer ')[1].strip())

    if not user or not user['status']['active']:
        return await errors.error(418, 'Invalid or inactive NovaAI API key!', 'Create a new NovaOSS API key or reactivate your account.')

    ban_reason = user['status']['ban_reason']
    if ban_reason:
        return await errors.error(403, f'Your NovaAI account has been banned. Reason: \'{ban_reason}\'.', 'Contact the staff for an appeal.')

    is_enterprise_key = 'enterprise' in user.get('role', 'default')

    if path.startswith('/enterprise/v1') and not is_enterprise_key:
        return await errors.error(403, 'Enterprise API is not available for your API key.', 'Contact the staff for an upgrade.')

    if 'account/credits' in path:
        return fastapi.responses.JSONResponse({'credits': user['credits']})

    if user['credits'] < 1:
        return await errors.error(429, 'Not enough credits.', 'Wait or earn more credits. Learn more on our website or Discord server.')

    if 'DISABLE_VARS' not in key_tags:
        payload_with_vars = json.dumps(payload)

        replace_dict = {
            'timestamp': str(int(time.time())),
            'date': time.strftime('%Y-%m-%d'),
            'time': time.strftime('%H:%M:%S'),
            'datetime': time.strftime('%Y-%m-%d %H:%M:%S'),
            'model': payload.get('model', 'unknown'),
        }

        if 'ALLOW_INSECURE_VARS' in key_tags:
            replace_dict.update({
                'my.ip': ip_address,
                'my.id': str(user['_id']),
                'my.role': user.get('role', 'default'),
                'my.credits': str(user['credits']),
                'my.discord': user.get('auth', {}).get('discord', ''),
            })

        for key, value in replace_dict.items():
            payload_with_vars = payload_with_vars.replace(f'[[{key}]]', value)

        payload = json.loads(payload_with_vars)

    policy_violation = False

    if not (moderation_debug_key and moderation_debug_key in key_tags and 'gpt-3' in payload.get('model', '')):
        if '/moderations' not in path:
            inp = ''

            if 'input' in payload or 'prompt' in payload:
                inp = payload.get('input', payload.get('prompt', ''))

            if isinstance(payload.get('messages'), list):
                inp = ''

                for message in payload.get('messages', []):
                    if message.get('role') == 'user':
                        inp += message.get('content', '') + '\n'

            if 'functions' in payload:
                inp += '\n'.join([function.get('description', '') for function in payload.get('functions', [])])

            if inp and len(inp) > 2 and not inp.isnumeric():
                policy_violation = await moderation.is_policy_violated(inp)

    if policy_violation:
        return await errors.error(
            400, f'The request contains content which violates this model\'s policies for <{policy_violation}>.',
            'We currently don\'t support any NSFW models.'
        )

    if 'chat/completions' in path and not payload.get('stream', False):
        payload['stream'] = False
    if 'chat/completions' in path and not payload.get('model'):
        payload['model'] = 'gpt-3.5-turbo'

    media_type = 'text/event-stream' if payload.get('stream', False) else 'application/json'

    if (model := payload.get('model')) not in models and model is not None:
        return await errors.error(404, 'Model not found.', 'Check the model name and try again.')

    return fastapi.responses.StreamingResponse(
        content=responder.respond(
            user=user,
            path=path,
            payload=payload,
            incoming_request=incoming_request,
        ),
        media_type=media_type
    )
