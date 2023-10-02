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

## Recommended
- `git` (for updates)
- `screen` (for production)
- Cloudflare (for security, anti-DDoS, etc.) - we fully support Cloudflare

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

### Proxy
- `PROXY_TYPE` (optional, defaults to `socks.PROXY_TYPE_HTTP`): the type of proxy - can be `http`, `https`, `socks4`, `socks5`, `4` or `5`, etc... 
- `PROXY_HOST`: the proxy host (host domain or IP address), without port!
- `PROXY_PORT` (optional)
- `PROXY_USER` (optional)
- `PROXY_PASS` (optional)

Want to use a proxy list? See the according section!
Keep in mind to set `USE_PROXY_LIST` to `True`! Otherwise, the proxy list won't be used.

### Proxy Lists
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
`TEST_NOVA_KEY` is the API key the which is used in tests. It should be one with tons of credits.

### Webhooks
`DISCORD_WEBHOOK__USER_CREATED` is the Discord webhook URL for when a user is created.
`DISCORD_WEBHOOK__API_ISSUE` is the Discord webhook URL for when an API issue occurs.

### Other
`KEYGEN_INFIX` can be almost any string (avoid spaces or special characters) - this string will be put in the middle of every NovaAI API key which is generated. This is useful for identifying the source of the key using e.g. RegEx.

## Run
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

## Adding a provider
To be documented!]

## Run tests
Make sure the API server is running on the port you specified and run:
`python checks`

## Default Ports
```yml
2332: Developement
2333: Production
```

## Production

Make sure your server is secure and up to date.
Check everything.

The following command will run the API  __without__ a reloader!

```bash
python run prod
```

or 

```bash
./screen.sh
```