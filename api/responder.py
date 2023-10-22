"""This module contains the streaming logic for the API."""

import os
import json
import yaml
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
from helpers.tokens import count_tokens_for_messages

load_dotenv()

CRITICAL_API_ERRORS = ['invalid_api_key', 'account_deactivated']
keymanager = providerkeys.manager
background_tasks: Set[asyncio.Task[Any]] = set()

with open(os.path.join('config', 'config.yml'), encoding='utf8') as f:
    config = yaml.safe_load(f)

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
    incoming_request: starlette.requests.Request=None,
):
    """
    Stream the completions request. Sends data in chunks
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

    skipped_errors = {
        'no_provider_key': 0,
        'insufficient_quota': 0,
        'billing_not_active': 0,
        'critical_provider_error': 0,
        'timeout': 0,
        'other_errors': []
    }

    input_tokens = 0
    output_tokens = 0

    for _ in range(10):
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
            skipped_errors['no_provider_key'] += 1
            continue

        target_request['headers'].update(target_request.get('headers', {}))

        if target_request['method'] == 'GET' and not payload:
            target_request['payload'] = None

        connector = None

        if os.getenv('PROXY_HOST') or os.getenv('USE_PROXY_LIST', 'False').lower() == 'true':
            connector = proxies.get_proxy().connector

        async with aiohttp.ClientSession(connector=connector) as session:
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
                            skipped_errors['insufficient_quota'] += 1
                            continue

                        if error_code == 'billing_not_active':
                            print('[!] billing not active')
                            await keymanager.deactivate_key(provider_name, provider_key, 'billing_not_active')
                            skipped_errors['billing_not_active'] += 1
                            continue

                        critical_error = False
                        for error in CRITICAL_API_ERRORS:
                            if error in str(client_json_response):
                                await keymanager.deactivate_key(provider_name, provider_key, error)
                                critical_error = True

                        if critical_error:
                            print('[!] critical provider error')
                            skipped_errors['critical_provider_error'] += 1
                            continue

                        if response.ok:
                            if is_chat and not is_stream:
                                input_tokens = client_json_response['usage']['prompt_tokens']
                                output_tokens = client_json_response['usage']['completion_tokens']

                            server_json_response = client_json_response
                    elif response.content_type == 'text/plain':
                        data = (await response.read()).decode("utf-8")
                        print(f'[!] {data}')
                        skipped_errors['other_errors'] = skipped_errors['other_errors'].append(data)
                        continue

                    if is_stream:
                        input_tokens = await count_tokens_for_messages(payload['messages'], model=model)

                        chunk_no = 0
                        buffer = ''

                        async for chunk in response.content.iter_chunked(1024):
                            chunk_no += 1

                            chunk = chunk.decode('utf8')

                            if 'azure' in provider_name:
                                chunk = chunk.replace('data: ', '', 1)

                                if not chunk.strip() or chunk_no == 1:
                                    continue

                            subchunks = chunk.split('\n\n')
                            buffer += subchunks[0]

                            for subchunk in [buffer] + subchunks[1:-1]:
                                if not subchunk.startswith('data: '):
                                    subchunk = 'data: ' + subchunk

                                yield subchunk + '\n\n'

                            buffer = subchunks[-1]

                        output_tokens = chunk_no
                    break

            except aiohttp.client_exceptions.ServerTimeoutError:
                skipped_errors['timeout'] += 1
                continue

    else:
        skipped_errors = {k: v for k, v in skipped_errors.items() if ((isinstance(v, list) and len(v) > 0) or v > 0)}
        skipped_errors = ujson.dumps(skipped_errors, indent=4)
        yield await errors.yield_error(500,
            f'Sorry, our API seems to have issues connecting to "{model}".',
            f'Please send this info to support: {skipped_errors}'
        )
        return

    if (not is_stream) and server_json_response:
        yield json.dumps(server_json_response)

    role = user.get('role', 'default')

    model_multipliers = config['costs']
    model_multiplier = model_multipliers['other']

    if is_chat:
        model_multiplier = model_multipliers['chat-models'].get(payload.get('model'), model_multiplier)
        total_tokens = input_tokens + output_tokens
        credits_cost = total_tokens / 60
        credits_cost = round(credits_cost * model_multiplier)

        if credits_cost < 1:
            credits_cost = 1

        tokens = {
            'input': input_tokens,
            'output': output_tokens,
            'total': total_tokens
        }
    else:
        credits_cost = 5
        tokens = {
            'input': 0,
            'output': 0,
            'total': credits_cost
        }

    try:
        role_cost_multiplier = config['roles'][role]['bonus']
    except KeyError:
        role_cost_multiplier = 1

    credits_cost = round(credits_cost * role_cost_multiplier)

    print(f'[bold]Credits cost[/bold]: {credits_cost}')

    create_background_task(
        after_request.after_request(
            provider=provider_name,
            incoming_request=incoming_request,
            target_request=target_request,
            user=user,
            credits_cost=credits_cost,
            tokens=tokens,
            path=path,
            is_chat=is_chat,
            model=model,
        )
    )
