"""Tests the API."""

import os
import time
import json
import httpx
import openai
import asyncio
import traceback

from rich import print
from typing import List
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()

MODEL = 'gpt-3.5-turbo'

MESSAGES = [
    {
        'role': 'user',
        'content': 'Just respond with the number "1337", nothing else.'
    }
]

api_endpoint = os.getenv('CHECKS_ENDPOINT', 'http://localhost:2332/v1')
# api_endpoint = 'http://localhost:2333/v1'

async def _response_base_check(response: httpx.Response) -> None:
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise ConnectionError(f'API returned an error: {response.json()}') from exc

async def test_server():
    """Tests if the API server is running."""

    try:
        request_start = time.perf_counter()
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url=f'{api_endpoint.replace("/v1", "")}',
                timeout=3
            )
            await _response_base_check(response)

        assert response.json()['ping'] == 'pong', 'The API did not return a correct response.'
    except httpx.ConnectError as exc:
        raise ConnectionError(f'API is not running on port {api_endpoint}.') from exc

    else:
        return time.perf_counter() - request_start

async def test_chat_non_stream_gpt4() -> float:
    """Tests non-streamed chat completions with the GPT-4 model."""

    json_data = {
        'model': 'gpt-4',
        'messages': MESSAGES,
        'stream': False
    }

    request_start = time.perf_counter()

    async with httpx.AsyncClient() as client:
        response = await client.post(
            url=f'{api_endpoint}/chat/completions',
            headers=HEADERS,
            json=json_data,
            timeout=10,
        )
        await _response_base_check(response)

    assert '1337' in response.json()['choices'][0]['message']['content'], 'The API did not return a correct response.'
    return time.perf_counter() - request_start

async def test_chat_stream_gpt3() -> float:
    """Tests the text stream endpoint with the GPT-3.5-Turbo model."""

    json_data = {
        'model': 'gpt-3.5-turbo',
        'messages': MESSAGES,
        'stream': True,
    }

    request_start = time.perf_counter()

    async with httpx.AsyncClient() as client:
        response = await client.post(
            url=f'{api_endpoint}/chat/completions',
            headers=HEADERS,
            json=json_data,
            timeout=10,
        )
        await _response_base_check(response)

    chunks = []
    resulting_text = ''

    async for chunk in response.aiter_text():
        for subchunk in chunk.split('\n\n'):
            chunk = subchunk.replace('data: ', '', 1).strip()

            if chunk == '[DONE]':
                break

            if chunk:
                chunks.append(json.loads(chunk))

                try:
                    resulting_text += json.loads(chunk)['choices'][0]['delta']['content']
                except KeyError:
                    pass

    assert '1337' in resulting_text, 'The API did not return a correct response.'

    return time.perf_counter() - request_start

async def test_image_generation() -> float:
    """Tests the image generation endpoint with the SDXL model."""

    json_data = {
        'prompt': 'a nice sunset with a samurai standing in the middle',
        'n': 1,
        'size': '1024x1024'
    }

    request_start = time.perf_counter()

    async with httpx.AsyncClient() as client:
        response = await client.post(
            url=f'{api_endpoint}/images/generations',
            headers=HEADERS,
            json=json_data,
            timeout=10,
        )
        await _response_base_check(response)

    assert '://' in response.json()['data'][0]['url']
    return time.perf_counter() - request_start

class StepByStepAIResponse(BaseModel):
    """Demo response structure for the function calling test."""
    title: str
    steps: List[str]

async def test_function_calling():
    """Tests function calling functionality with newer GPT models."""

    json_data = {
        'stream': False,
        'model': 'gpt-3.5-turbo-0613',
        'messages': [
            {"role": "user", "content": "Explain how to assemble a PC"}
        ],
        'functions': [
            {
                'name': 'get_answer_for_user_query',
                'description': 'Get user answer in series of steps',
                'parameters': StepByStepAIResponse.schema()
            }
        ],
        'function_call': {'name': 'get_answer_for_user_query'}
    }

    request_start = time.perf_counter()

    async with httpx.AsyncClient() as client:
        response = await client.post(
            url=f'{api_endpoint}/chat/completions',
            headers=HEADERS,
            json=json_data,
            timeout=15,
        )
        await _response_base_check(response)

    res = response.json()
    output = json.loads(res['choices'][0]['message']['function_call']['arguments'])
    print(output)

    assert output.get('title') and output.get('steps'), 'The API did not return a correct response.'
    return time.perf_counter() - request_start

async def test_models():
    """Tests the models endpoint."""

    request_start = time.perf_counter()
    async with httpx.AsyncClient() as client:
        response = await client.get(
            url=f'{api_endpoint}/models',
            headers=HEADERS,
            timeout=3
        )
        await _response_base_check(response)
        res = response.json()

    all_models = [model['id'] for model in res['data']]

    assert 'gpt-3.5-turbo' in all_models, 'The model gpt-3.5-turbo is not present in the models endpoint.'
    return time.perf_counter() - request_start

# ==========================================================================================

async def demo():
    """Runs all tests."""

    try:
        for _ in range(30):
            if await test_server():
                break

            print('Waiting until API Server is started up...')
            time.sleep(1)
        else:
            raise ConnectionError('API Server is not running.')

        for func in [
            test_chat_non_stream_gpt4,
            test_chat_stream_gpt3
        ]:
            print(f'[*] {func.__name__}')
            result = await func()
            print(f'[+] {func.__name__} - {result}')

    except Exception as exc:
        print('[red]Error: ' + str(exc))
        traceback.print_exc()
        exit(500)

openai.api_base = api_endpoint
openai.api_key = os.environ['NOVA_KEY']

HEADERS = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer ' + openai.api_key
}

if __name__ == '__main__':
    asyncio.run(demo())
