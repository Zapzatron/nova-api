"""FastAPI setup."""

import fastapi
import pydantic

from rich import print
from dotenv import load_dotenv

from bson.objectid import ObjectId

from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from fastapi.middleware.cors import CORSMiddleware
from slowapi.util import get_remote_address
from slowapi import Limiter, _rate_limit_exceeded_handler

import core
import handler

load_dotenv()

app = fastapi.FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*']
)

app.include_router(core.router)

limiter = Limiter(
    swallow_errors=True,
    key_func=get_remote_address,
    default_limits=[
    '2/second',
    '30/minute',
    '400/hour'
])

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

@app.on_event('startup')
async def startup_event():
    """Runs when the API starts up."""
    # https://stackoverflow.com/a/74529009
    pydantic.json.ENCODERS_BY_TYPE[ObjectId]=str

@app.get('/')
async def root():
    """
    Returns general information about the API.
    """

    return {
        'hi': 'Welcome to the Nova API!',
        'learn_more_here': 'https://nova-oss.com',
        'github': 'https://github.com/novaoss/nova-api',
        'core_api_docs_for_nova_developers': '/docs',
        'ping': 'pong'
    }

@app.route('/v1/{path:path}', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
async def v1_handler(request: fastapi.Request):
    res = await handler.handle(incoming_request=request)
    return res

@limiter.limit('100/minute', '1000/hour') 
@app.route('/enterprise/v1/{path:path}', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
async def enterprise_handler(request: fastapi.Request):
    res = await handler.handle(incoming_request=request)
    return res
