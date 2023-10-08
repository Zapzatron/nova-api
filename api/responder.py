"""This module contains the streaming logic for the API."""

import os
import json
import ujson
import aiohttp
import asyncio
import starlette

from typing import Any, Coroutine, Set
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

background_tasks: Set[asyncio.Task[Any]] = set()


def create_background_task(coro: Coroutine[Any, Any, Any]) -> None:
    """asyncio.create_task, which prevents the task from being garbage collected.

    https://docs.python.org/3/library/asyncio-task.html#asyncio.create_task
    """
    task = asyncio.create_task(coro)
    background_tasks.add(task)
    task.add_done_callback(background_tasks.discard)


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

    if 'chat/completions' in path:
        is_chat = True
        model = payload['model']

    server_json_response = {}

    headers = {
        'Content-Type': 'application/json'
    }

    for i in range(5):
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

        if provider_key == '--NO_KEY--':
            print(f'No key for {provider_name}')
            yield await errors.yield_error(500,
                'Sorry, our API seems to have issues connecting to our provider(s).',
                'This most likely isn\'t your fault. Please try again later.'
            )
            return

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
                        connect=0.75,
                        total=float(os.getenv('TRANSFER_TIMEOUT', '500'))
                    )
                ) as response:
                    is_stream = response.content_type == 'text/event-stream'

                    if response.content_type == 'application/json':
                        client_json_response = await response.json()

                        try:
                            error_code = client_json_response['error']['code']
                        except KeyError:
                            error_code = ''

                        if error_code == 'method_not_supported':
                            yield await errors.yield_error(400, 'Sorry, this endpoint does not support this method.', 'Please use a different method.')

                        if error_code == 'insufficient_quota':
                            print('[!] insufficient quota')
                            await keymanager.rate_limit_key(provider_name, provider_key, 86400)
                            continue

                        if error_code == 'billing_not_active':
                            print('[!] billing not active')
                            await keymanager.deactivate_key(provider_name, provider_key, 'billing_not_active')
                            continue

                        critical_error = False
                        for error in CRITICAL_API_ERRORS:
                            if error in str(client_json_response):
                                await keymanager.deactivate_key(provider_name, provider_key, error)
                                critical_error = True
                        
                        if critical_error:
                            print('[!] critical error')
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

                        chunk_no = 0
                        buffer = ''

                        async for chunk  in response.content.iter_chunked(1024):
                            chunk_no += 1

                            chunk = chunk.decode('utf8')

                            if 'azure' in provider_name:
                                chunk = chunk.replace('data: ', '')

                                if not chunk or chunk_no == 1:
                                    continue

                            subchunks = chunk.split('\n\n')
                            buffer += subchunks[0]

                            yield buffer + '\n\n'
                            buffer = subchunks[-1]

                            for subchunk in subchunks[1:-1]:
                                yield subchunk + '\n\n'

                    break

            except aiohttp.client_exceptions.ServerTimeoutError:
                continue

    else:
        yield await errors.yield_error(500, 'Sorry, our API seems to have issues connecting to our provider(s).', 'This most likely isn\'t your fault. Please try again later.')
        return

    if (not is_stream) and server_json_response:
        yield json.dumps(server_json_response)

    create_background_task(
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
