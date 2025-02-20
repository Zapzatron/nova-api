import time
import asyncio
import tiktoken

async def count_tokens_for_messages(messages: list, model: str='gpt-3.5-turbo-0613') -> int:
    """Return the number of tokens used by a list of messages

    Args:
        messages (list): _description_
        model (str, optional): _description_. Defaults to 'gpt-3.5-turbo-0613'.

    Raises:
        NotImplementedError: _description_

    Returns:
        int: _description_
    """

    try:
        encoding = tiktoken.encoding_for_model(model)

    except KeyError:
        encoding = tiktoken.get_encoding('cl100k_base')

    if model in {
        'gpt-3.5-turbo-0613',
        'gpt-3.5-turbo-16k-0613',
        'gpt-4-0314',
        'gpt-4-32k-0314',
        'gpt-4-0613',
        'gpt-4-32k-0613',
    }:
        tokens_per_message = 3
        tokens_per_name = 1

    elif model == 'gpt-3.5-turbo-0301':
        tokens_per_message = 4  # every message follows <|start|>{role/name}\n{content}<|end|>\n
        tokens_per_name = -1  # if there's a name, the role is omitted

    elif 'gpt-3.5-turbo' in model:
        return await count_tokens_for_messages(messages, model='gpt-3.5-turbo-0613')

    elif 'gpt-4' in model:
        return await count_tokens_for_messages(messages, model='gpt-4-0613')

    else:
        raise NotImplementedError(f"""count_tokens_for_messages() is not implemented for model {model}.
See https://github.com/openai/openai-python/blob/main/chatml.md
for information on how messages are converted to tokens.""")
    
    num_tokens = 0
    for message in messages:
        num_tokens += tokens_per_message
        for key, value in message.items():
            num_tokens += len(encoding.encode(value))
            if key == 'name':
                num_tokens += tokens_per_name

    num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>

    return num_tokens

if __name__ == '__main__':
    start = time.perf_counter()

    messages = [
        {
            'role': 'user',
            'content': 'Hi'
        }
    ]
    print(asyncio.run(count_tokens_for_messages(messages)))
    print(f'Took {(time.perf_counter() - start) * 1000}ms')
