import os
import sys

from rich import print

def remove_duplicate_keys(file):
    with open(file, 'r', encoding='utf8') as f:
        lines = f.readlines()

    unique_lines = set(lines)

    with open(file, 'w', encoding='utf8') as f:
        f.writelines(unique_lines)

try:
    provider_name = sys.argv[1]

    if provider_name == '--clear':
        for file in os.listdir('secret/'):
            if file.endswith('.txt'):
                remove_duplicate_keys(f'secret/{file}')

        exit()

except IndexError:
    print('List of available providers:')

    for file_name in os.listdir(os.path.dirname(__file__)):
        if file_name.endswith('.py') and not file_name.startswith('_'):
            print(file_name.split('.')[0])

    sys.exit(0)

try:
    provider = __import__(provider_name)
except ModuleNotFoundError as exc:
    print(f'Provider "{provider_name}" not found.')
    print('Available providers:')
    for file_name in os.listdir(os.path.dirname(__file__)):
        if file_name.endswith('.py') and not file_name.startswith('_'):
            print(file_name.split('.')[0])
    sys.exit(1)

if len(sys.argv) > 2:
    model = sys.argv[2]
else:
    model = provider.MODELS[-1]


print(f'{provider_name} @ {model}')
comp = provider.chat_completion(model=model)
print(comp)
