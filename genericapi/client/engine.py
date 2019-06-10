from __future__ import annotations
from typing import AsyncContextManager, AsyncIterator
from contextlib import asynccontextmanager
import asyncio

from aiohttp import ClientSession, ClientResponse
import aiolog


class RequestEngine:
    '''RequestEngine takes care of all request issuance'''
    __slots__ = ('_baseurl', '_sess')
    def __init__(self, baseurl: str) -> None:
        self._baseurl = baseurl
        self._sess: ClientSession

    async def __aenter__(self) -> RequestEngine:
        await self.open()
        return self

    async def open(self) -> None:
        '''Opens aiohttp.ClientSession'''
        aiolog.start(loop=asyncio.get_event_loop())
        self._sess = ClientSession()

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    async def close(self) -> None:
        '''
        Close underlying aiohttp.ClientSession
        and asynchroneous logging
        '''
        await self._sess.close()
        await aiolog.stop()

    @asynccontextmanager
    async def issue(self, method: str, path: str, **kw) -> AsyncIterator[ClientResponse]:
        '''A generic request issue method'''
        url = f'{self._baseurl}{path}'
        async with self._sess.request(method, url, **kw) as res:
            yield res

    def post(self, *a, **kw) -> AsyncContextManager[ClientResponse]:
        '''Issues a post request'''
        return self.issue('POST', *a, **kw)

    def get(self, *a, **kw) -> AsyncContextManager[ClientResponse]:
        '''Issues a get request'''
        return self.issue('GET', *a, **kw)

    def put(self, *a, **kw) -> AsyncContextManager[ClientResponse]:
        '''Issues a put request'''
        return self.issue('PUT', *a, **kw)

    def delete(self, *a, **kw) -> AsyncContextManager[ClientResponse]:
        '''Issues a delete request'''
        return self.issue('DELETE', *a, **kw)

    def head(self, *a, **kw) -> AsyncContextManager[ClientResponse]:
        '''Issues a head request'''
        return self.issue('HEAD', *a, **kw)
