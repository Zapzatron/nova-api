import os
import time

from dotenv import load_dotenv
from slowapi.util import get_remote_address

load_dotenv()

def get_ip(request) -> str:
    """Get the IP address of the incoming request."""

    detected_ip = request.headers.get('cf-connecting-ip', get_remote_address(request))
    return detected_ip

def get_ratelimit_key(request) -> str:
    """Get the IP address of the incoming request."""
    
    ip = get_ip(request)
    return ip
