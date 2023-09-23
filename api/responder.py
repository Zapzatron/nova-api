"""This module contains the streaming logic for the API."""

import os
import json
import random
import aiohttp
import starlette

from rich import print
from dotenv import load_dotenv

import proxies
import provider_auth
import after_request
import load_balancing

from helpers import network, chat, errors
from db import key_validation

load_dotenv()

async def respond(
    path: str='/v1/chat/completions',
    user: dict=None,
    payload: dict=None,
    credits_cost: int=0,
    input_tokens: int=0,
    incoming_request: starlette.requests.Request=None,
):
    """Stream the completions request. Sends data in chunks
    If not streaming, it sends the result in its entirety.
    """

    is_chat = False

    model = None
    is_stream = False

    if 'chat/completions' in path:
        is_chat = True
        model = payload['model']

    json_response = {}

    headers = {
        'Content-Type': 'application/json'
    }

    for i in range(20):
        # Load balancing: randomly selecting a suitable provider
        # If the request is a chat completion, then we need to load balance between chat providers
        # If the request is an organic request, then we need to load balance between organic providers
        try:
            if is_chat:
                target_request = await load_balancing.balance_chat_request(payload)
            else:
                
                # In this case we are doing a organic request. "organic" means that it's not using a reverse engineered front-end, but rather ClosedAI's API directly
                # churchless.tech is an example of an organic provider, because it redirects the request to ClosedAI.
                target_request = await load_balancing.balance_organic_request({
                    'method': incoming_request.method,
                    'path': path,
                    'payload': payload,
                    'headers': headers,
                    'cookies': incoming_request.cookies
                })
        except ValueError as exc:
            yield await errors.yield_error(500, f'Sorry, the API has no active API keys for {model}.', 'Please use a different model.')
            return

        target_request['headers'].update(target_request.get('headers', {}))

        if target_request['method'] == 'GET' and not payload:
            target_request['payload'] = None

        # We haven't done any requests as of right now, everything until now was just preparation
        # Here, we process the request
        async with aiohttp.ClientSession(connector=proxies.get_proxy().connector) as session:
            try:
                async with session.request(
                    method=target_request.get('method', 'POST'),
                    url=target_request['url'],
                    data=target_request.get('data'),
                    json=target_request.get('payload'),
                    headers=target_request.get('headers', {}),
                    cookies=target_request.get('cookies'),
                    ssl=False,
                    timeout=aiohttp.ClientTimeout(
                        connect=0.5,
                        total=float(os.getenv('TRANSFER_TIMEOUT', '500'))
                    ),
                ) as response:
                    is_stream = response.content_type == 'text/event-stream'

                    if response.status == 429:
                        continue

                    if response.content_type == 'application/json':
                        data = await response.json()

                        error = data.get('error')
                        match error:
                            case None:
                                pass

                            case _:
                                match error.get('code'):
                                    case "insufficient_quota":
                                        key = target_request.get('provider_auth')
                                        await key_validation.log_rated_key(key)
                                        continue

                                    case _:
                                        pass

                        if 'method_not_supported' in str(data):
                            await errors.error(500, 'Sorry, this endpoint does not support this method.', data['error']['message'])

                        if 'invalid_api_key' in str(data) or 'account_deactivated' in str(data):
                            print('[!] invalid api key', target_request.get('provider_auth'))
                            await provider_auth.invalidate_key(target_request.get('provider_auth'))
                            continue

                        if response.ok:
                            json_response = data

                    if is_stream:
                        try:
                            response.raise_for_status()
                        except Exception as exc:
                            if 'Too Many Requests' in str(exc):
                                print('[!] too many requests')
                                continue

                        async for chunk in response.content.iter_any():
                            chunk = chunk.decode('utf8').strip()
                            yield chunk + '\n\n'

                    break

            except Exception as exc:
                continue

            if (not json_response) and is_chat:
                print('[!] chat response is empty')
                continue
    else:
        print('[!] no response')
        yield await errors.yield_error(500, 'Sorry, the provider is not responding.', 'Please try again later.')
        return

    if (not is_stream) and json_response:
        yield json.dumps(json_response)

    await after_request.after_request(
        incoming_request=incoming_request,
        target_request=target_request,
        user=user,
        credits_cost=credits_cost,
        input_tokens=input_tokens,
        path=path,
        is_chat=is_chat,
        model=model,
    )
