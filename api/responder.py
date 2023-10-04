"""This module contains the streaming logic for the API."""

import os
import json
import logging
import aiohttp
import asyncio
import starlette

from rich import print
from dotenv import load_dotenv

import proxies
import after_request
import load_balancing

from helpers import errors
from db import providerkeys

load_dotenv()

CRITICAL_API_ERRORS = ['invalid_api_key', 'account_deactivated']

keymanager = providerkeys.manager

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

    server_json_response = {}

    headers = {
        'Content-Type': 'application/json'
    }

    for _ in range(20):
        # Load balancing: randomly selecting a suitable provider
        try:
            if is_chat:
                target_request = await load_balancing.balance_chat_request(payload)
            else:
                target_request = await load_balancing.balance_organic_request({
                    'method': incoming_request.method,
                    'path': path,
                    'payload': payload,
                    'headers': headers,
                    'cookies': incoming_request.cookies
                })
        except ValueError:
            yield await errors.yield_error(500, f'Sorry, the API has no active API keys for {model}.', 'Please use a different model.')
            return

        provider_auth = target_request.get('provider_auth')

        if provider_auth:
            provider_name = provider_auth.split('>')[0]
            provider_key = provider_auth.split('>')[1]

        target_request['headers'].update(target_request.get('headers', {}))

        if target_request['method'] == 'GET' and not payload:
            target_request['payload'] = None

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
                        connect=1.0,
                        total=float(os.getenv('TRANSFER_TIMEOUT', '500'))
                    ),
                ) as response:
                    is_stream = response.content_type == 'text/event-stream'

                    if response.status == 429:
                        await keymanager.rate_limit_key(provider_name, provider_key)
                        continue

                    if response.content_type == 'application/json':
                        client_json_response = await response.json()

                        if 'method_not_supported' in str(client_json_response):
                            await errors.error(500, 'Sorry, this endpoint does not support this method.', data['error']['message'])

                        critical_error = False
                        for error in CRITICAL_API_ERRORS:
                            if error in str(client_json_response):
                                await keymanager.deactivate_key(provider_name, provider_key, error)
                                critical_error = True
                        
                        if critical_error:
                            continue

                        if response.ok:
                            server_json_response = client_json_response

                        else:
                            continue

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
                print('[!] exception', exc)
                if 'too many requests' in str(exc):
                    #!TODO
                    pass

                continue

    else:
        yield await errors.yield_error(500, 'Sorry, our API seems to have issues connecting to our provider(s).', 'This most likely isn\'t your fault. Please try again later.')
        return

    if (not is_stream) and server_json_response:
        yield json.dumps(server_json_response)

    asyncio.create_task(
        after_request.after_request(
            incoming_request=incoming_request,
            target_request=target_request,
            user=user,
            credits_cost=credits_cost,
            input_tokens=input_tokens,
            path=path,
            is_chat=is_chat,
            model=model,
        )
    )
