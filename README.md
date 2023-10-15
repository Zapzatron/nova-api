# ☄️ NovaAI - Core API Server
API server for accessing AI models.

![Badge showing the most used language](https://img.shields.io/github/languages/top/novaoss/nova-api)
![Badge showing the code size](https://img.shields.io/github/languages/code-size/novaoss/nova-api)
![Discord Badge](https://img.shields.io/discord/1120037287300976640)
![Badge showing the number of issues](https://img.shields.io/github/issues/novaoss/nova-api)
![Badge showing the number of pull requests](https://img.shields.io/github/issues-pr/novaoss/nova-api)
![Badge showing the license](https://img.shields.io/github/license/novaoss/nova-api)

![Badge showing the number of stars](https://img.shields.io/github/stars/novaoss/nova-api?style=social)
![Badge showing the number of forks](https://img.shields.io/github/forks/novaoss/nova-api?style=social)
![Badge showing the number of watchers](https://img.shields.io/github/watchers/novaoss/nova-api?style=social)

:purple_heart: **We rely on support to keep our services free.** If you want to support us, you can donate to us using the following methods:

![Donation QR-Codes with the caption "Support open source development"](https://i.ibb.co/Xx71btm/image.png)
![Nova-API Conver/Banner Image - a picture of a galaxy with the caption "the core API server"](https://i.ibb.co/ZBhkS56/nova-api.png)


## Star History

![Star history chart of NovaAI](https://api.star-history.com/svg?repos=NovaOSS/nova-api&theme=dark))

## NovaOSS APIs
Our infrastructure might seem a bit confusing, but it's actually quite simple. Just the first one really matters for you, if you want to access our AI API. The other ones are just for the team.

### AI API
**Public** (everyone can use it with a valid API key)

Endpoint: `https://api.nova-oss.com/v1/...`
Documentation & info: [nova-oss.com](https://nova-oss.com)

- Access to AI models

***

### User/Account management API
**Private** (NovaOSS operators only!)

Endpoint: `https://api.nova-oss.com/...`
Documentation: [api.nova-oss.com/docs](https://api.nova-oss.com/docs)

- Access to user accounts
- Implemented in [NovaCord](https://nova-oss.com/novacord)

### NovaCord Bot API
**Private** (NovaOSS operators only!)

Endpoint: `http://0.0.0.0:3224/...`

- acess to Discord server member roles (for receiving the Discord level, ...)
- hosted using [NovaCord](https://nova-oss.com/novacord)

### Website API
**Private** (NovaOSS operators only!)

Endpoint: `https://nova-oss.com/api/...`

This one's code can be found in the following repository: [github.com/novaoss/nova-web](https://github.com/novaoss/nova-web)

- Used for the Terms of Service (ToS) verification for the Discord bot.
- In a different repository and with a different domain because it needs to display codes on the website.
- Implemented in [NovaCord](https://nova-oss.com/novacord)

# Setup
## Requirements
- Python 3.9+
- pip
- MongoDB database
- `uvicorn`

## Recommended
- Setup of the other infrastructure
- `git` (for updates)
- `screen` (for production)
- Cloudflare (for security, anti-DDoS, etc.) - we fully support Cloudflare

## Staging System
This repository has an integrated staging system. It's a simple system that allows you to test the API server before deploying it to production.

You should definitely set up two databases on MongoDB: `nova-core` and `nova-test`. Please note that `nova-core` is always used for `providerkeys`.

Put your production `.env` file in `env/.prod.env`. Your test `.env` file should be in `.env`.

Running `PUSH_TO_PRODUCTION.sh` will:
- kill port `2333` (production)
- remove all contents of the production directory, set to `/home/nova-prod/` (feel free to change it)
- then copy the test directory (generally *this* directory) to the production directory
- copy the `.env` file from `env/.prod.env` to `.env`
- use `screen` to run the production server on port `2333`

## Install
Assuming you have a new version of Python 3.9+ and pip installed:
```py
python -m pip install -r requirements.txt
```

If you still get a `ModuleNotFoundError`s, you can forefully install the dependencies using:
```py
python -m pip install pipreqs
python -m pipreqs.pipreqs --force --mode no-pin
python -m pip install --upgrade -r requirements.txt
```

You can also try installing Nova API using `setup.py`:
```py
python setup.py
```

or 

```py
pip install .
```

***

Profanity checking requires:

```
pip install alt-profanity-check
# doesn't work? try
pip install git+https://github.com/dimitrismistriotis/alt-profanity-check.git
```

## `.env` configuration
Create a `.env` file, make sure not to reveal any of its contents to anyone, and fill in the required values in the format `KEY=VALUE`. Otherwise, the code won't run.

### Database
Set up a MongoDB database and set `MONGO_URI` to the MongoDB database connection URI. Quotation marks are definetly recommended here!

### Proxy (optional)
- `PROXY_TYPE` (optional, defaults to `socks.PROXY_TYPE_HTTP`): the type of proxy - can be `http`, `https`, `socks4`, `socks5`, `4` or `5`, etc... 
- `PROXY_HOST`: the proxy host (host domain or IP address), without port!
- `PROXY_PORT` (optional)
- `PROXY_USER` (optional)
- `PROXY_PASS` (optional)

Want to use a proxy list? See the according section!
Keep in mind to set `USE_PROXY_LIST` to `True`! Otherwise, the proxy list won't be used.

### Proxy Lists (optional)
To use proxy lists, navigate to `api/secret/proxies/` and create the following files:
- `http.txt`
- `socks4.txt`
- `socks5.txt`

Then, paste your proxies in the following format:

```
[username:password@]host:port
```
Whereas anything inside of `[]` is optional and the host can be an IP address or a hostname. Always specify the port.

If you're using [iproyal.com](https://iproyal.com?r=307932)<sup>affiliate link</sup>, follow the following steps:
- Order any type of proxy or proxies
- In the *Product Info* tab:
  - set *Select port* to `SOCKS5`
  - and *Select format* to `USER:PASS@IP:PORT`

#### Proxy List Examples
```
1.2.3.4:8080
user:pass@127.0.0.1:1337
aaaaaaaaaaaaa:bbbbbbbbbb@1.2.3.4:5555
```

In the proxy credential files, can use comments just like in Python.

**Important:** to activate the proxy lists, you need to change the `USE_PROXY_LIST` environment variable to `True`!


### ~~`ACTUAL_IPS` (optional)~~ (deprecated, might come back in the future)
This is a security measure to make sure a proxy, VPN, Tor or any other IP hiding service is used by the host when accessing "Closed"AI's API.
It is a space separated list of IP addresses that are allowed to access the API.
You can also just add the *beginning* of an API address, like `12.123.` (without an asterisk!) to allow all IPs starting with `12.123.`.
> To disable the warning if you don't have this feature enabled, set `ACTUAL_IPS` to `None`.

### Timeout
`TRANSFER_TIMEOUT` seconds to wait until the program throws an exception for if the request takes too long. We recommend rather long times like `500` for 500 seconds.

### Core Keys
`CORE_API_KEY` specifies the **very secret key** for  which need to access the entire user database etc.
`NOVA_KEY` is the API key the which is used in tests. It should be one with tons of credits.

### Webhooks
`DISCORD_WEBHOOK__USER_CREATED` is the Discord webhook URL for when a user is created.
`DISCORD_WEBHOOK__API_ISSUE` is the Discord webhook URL for when an API issue occurs.

### Other
`KEYGEN_INFIX` can be almost any string (avoid spaces or special characters) - this string will be put in the middle of every NovaAI API key which is generated. This is useful for identifying the source of the key using e.g. RegEx.

## Misc
`api/cache/models.json` has to be a valid JSON file in the OpenAI format. It is what `/v1/models` always returns. Make sure to update it regularly. 

Example: https://pastebin.com/raw/WuNzTJDr (updated ~aug/2023)

## Providers
This is one of the most essential parts of NovaAI. Providers are the APIs used to access the AI models.
The modules are located in `api/providers/` and active providers are specified in `api/providers/__init__.py`.

You shouldn't use `.env` for provider keys. Instead, use the database as it's more flexible and secure. For a detailed explanation, scroll down a bit to the database section.

Always return the `provider_auth` dictionary key if you a API key is required. Example:

```py
...
    return {
        ...
        'provider_auth': f'exampleprovider>{key}'
    }
...
```

Whereas `exampleprovider` is the provider name used in the database.

### Check providers
List all providers using `python api`. This **won't** start the API server.

Check if a provider is working using `python api <provider>`, e.g. `python api azure`. This **doesn't** require the API to be running.

## Core Database

You need to set up a MongoDB database and set `MONGO_URI` in `.env` to the MongoDB database connection URI. Use quotation marks!

It's also important to set up the database `nova-core`.

The following collections are used in the database and will be created automatically if they don't exist.

### `users`
Generally, the `api_key` should be treated as the primary key. However, the `discord` and `github` keys are also unique and can be used as primary keys.
- `api_key`: API key [str]
- `credits`: credits [int]
- `role` (optional): credit multiplier. Check `api/config/config.yml`. [str]
- `status`:
  - `active`: defaults to `true`. May be used in the future so that users can deactivate their accounts.
  - `ban_reason`: defaults to `""`. If the user is banned, this will be set to the reason.
- `auth`:
  - `discord`: Discord user ID. Use a string, because Discord IDs can be larger than the maximum integer value.
  - `github`: GitHub user ID. Not used yet.
- `level`: Discord (Arcane bot) level. [int]

### `providerkeys`
Used in `api/providers/...` to store API keys of the providers.

- `provider`: provider name [str], e.g. `azure``
- `key`: API key [str], e.g. `sk-...`
- `rate_limited_since`: timestamp [int], defaults to `null`. The unix timestamp when the provider was rate limited. If it's `null`, the provider is not rate limited.
- `inactive_reason`: defaults to `null`. If the key is disabled or terminated, this will be set to the reason automatically. You can also set it manually. [str]
- `source`: just to keep track of where the key came from. [str]

### `stats`
Logs general statistics.
Automatically updated by the API server.

More info is yet to be documented.

### `logs`
Every API request is logged here.
Automatically updated by the API server.

More info is yet to be documented.

## Finance Database
The finance database is used to keep track of the finances.

**Important:** *always* use the specified `currency` for the field `amount`.

### `donations`
- `currency`: (crypto) currency [str], e.g. EUR, USD, BTC, USDT-TRX, ...
- `amount`: amount [float].
- `user`: [str], Discord user ID
- `proof`: [str], link to proof (e.g. transaction hash)
- `timestamp`: [int], unix timestamp

### `expenses`
- `currency`: (crypto) currency [str], e.g. EUR, USD, BTC, USDT-ETH, ...
- `amount`: amount [float]. NOT negative!
- `proof`: [str], link to proof (e.g. transaction hash)
- `type`: [str], type of expense, e.g. `wage`, `payment`, `donation`, ...
- `to`: [str], entity the expense was paid to, e.g. `IPRoyal`, `employee/John`
- `reason`: [str], reason for the expense
- `timestamp`: [int], unix timestamp

## Run Test Server
> **Warning:** read the according section for production usage!

For developement:

```bash
python run
```

This will run the development server on port `2332`.

You can also specify a port, e.g.:

```bash
python run 1337
```
  
## Tests
Make sure the API server is running on the port you specified and run:
`python checks`

## Default Ports
It is recommended to use the default ports, because this will make it easier to set other parts of the infrastructure up.

```yml
2332: Developement
2333: Production
```

## Run Production Server

Make sure you have read all the according sections and have set up everything correctly.
