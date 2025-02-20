"""This module makes it easy to implement proxies by providing a class.."""

import os
import socket
import random
import aiohttp_socks

from rich import print
from dotenv import load_dotenv

load_dotenv()

USE_PROXY_LIST = os.getenv('USE_PROXY_LIST', 'False').lower() == 'true'

class Proxy:
    """
    Represents a proxy. 
    The type can be either http, https, socks4 or socks5.
    You can also pass a url, which will be parsed into the other attributes.
    
    URL format:
    [type]://[username:password@]host:port
    """

    def __init__(self,
        url: str=None,
        proxy_type: str='http',
        host_or_ip: str='127.0.0.1',
        port: int=8080,
        username: str=None,
        password: str=None
    ):
        if url:
            proxy_type = url.split('://')[0]
            url = url.split('://')[1]

            if '@' in url:
                username = url.split('@')[0].split(':')[0]
                password = url.split('@')[0].split(':')[1]

            host_or_ip = url.split('@')[-1].split(':')[0]
            port = int(url.split('@')[-1].split(':')[1])

        self.proxy_type = proxy_type
        self.host_or_ip = host_or_ip

        try:
            self.ip_address = socket.gethostbyname(self.host_or_ip) # get ip address from host
        except socket.gaierror:
            self.ip_address = self.host_or_ip

        self.host = self.host_or_ip
        self.port = port
        self.username = username
        self.password = password

        self.url = f'{self.proxy_type}://{self.username}:{self.password}@{self.host}:{self.port}'
        self.url_ip = f'{self.proxy_type}://{self.username}:{self.password}@{self.ip_address}:{self.port}'
        self.urls = {
            'http': self.url,
            'https': self.url
        }

        self.urls_httpx = {k + '://' :v for k, v in self.urls.items()}
        self.proxies = self.url

    @property
    def connector(self):
        """
        Returns a proxy connector
        Returns an aiohttp_socks.ProxyConnector object. 
        This can be used in aiohttp.ClientSession.
        """

        proxy_types = {
            'http': aiohttp_socks.ProxyType.HTTP,
            'https': aiohttp_socks.ProxyType.HTTP,
            'socks4': aiohttp_socks.ProxyType.SOCKS4,
            'socks5': aiohttp_socks.ProxyType.SOCKS5
        }

        return aiohttp_socks.ProxyConnector(
            proxy_type=proxy_types[self.proxy_type],
            host=self.host,
            port=self.port,
            rdns=False, 
            username=self.username,
            password=self.password
        )

## Load proxies from their files

proxies_in_files = []

for proxy_type in ['http', 'socks4', 'socks5']:
    try:
        with open(os.path.join('secret', 'proxies', f'{proxy_type}.txt')) as f:
            for line in f:
                clean_line = line.split('#', 1)[0].strip()
                if clean_line:
                    proxies_in_files.append(f'{proxy_type}://{clean_line}')
    except FileNotFoundError:
        pass

## Manages the proxy list

class ProxyLists:
    def __init__(self):
        random_proxy = random.choice(proxies_in_files)

        self.get_random = Proxy(url=random_proxy)
        self.connector = aiohttp_socks.ChainProxyConnector.from_urls(proxies_in_files)

def get_proxy() -> Proxy:
    """
    Returns a Proxy object
    The proxy is either from the proxy list or from the environment variables.
    """

    if USE_PROXY_LIST:
        return ProxyLists().get_random

    return Proxy(
        proxy_type=os.getenv('PROXY_TYPE', 'http'),
        host_or_ip=os.environ['PROXY_HOST'],
        port=int(os.getenv('PROXY_PORT', '8080')),
        username=os.getenv('PROXY_USER'),
        password=os.getenv('PROXY_PASS')
    )

if __name__ == '__main__':
    print(get_proxy().url)
