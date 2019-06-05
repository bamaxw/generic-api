from typing import Any, AsyncIterator, cast, Container, Dict, Optional, Type, Union
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass, field
from types import TracebackType
from datetime import datetime
import asyncio
import logging

from aiohttp import ClientResponse as Response, ClientSession as Session
from tenacity import retry, retry_if_exception_type

from crossroads import CrossRoads

from .json import json
from .utils import cache_for, minutes
from .config import SessionConfig, PolicyType
from .signals import ShouldRetry, return_from_signal

log = logging.getLogger(__name__)


class Client:
    # Client allows some attributes to be set in a declarative way
    # like so
    # Client attributes
    __slots__ = ('_service_name', '_prefix', '_host', 'env', 'config', '__resolving',
                 '__resolved', '_static', '_session', 'retriable_issue', 'exceptions')
    host: Optional[str] = None
    service_name: Optional[str] = None
    prefix: str = ''
    # Config attributes
    __config_fields__ = ('retry_codes', 'retry_policy', 'timeout')
    retry_codes: Optional[Container[Union[str, int]]]
    retry_policy: Dict[str, PolicyType]
    timeout: int
    exceptions: Dict[str, Type[Exception]]
    def __init__(self,
                 env: Optional[str] = None,
                 *,
                 service_name: Optional[str] = None,
                 prefix: str = '',
                 host: Optional[str] = None,
                 config: Union[None, Dict[str, Any], SessionConfig] = None,
                 exceptions: Optional[Dict[str, Type[Exception]]] = None) -> None:
        # Validate arguments
        if self.service_name and service_name:
            raise TypeError("'service_name' specified at both class and instance level")
        if self.prefix and prefix:
            raise TypeError("'prefix' specified at both class and instance level")
        # Validate config type
        if isinstance(config, (dict, type(None))):
            config = dict(self._get_cls_config(), **config or {})
            session_config = SessionConfig(**config)
        elif isinstance(config, SessionConfig):
            session_config = config
        else:
            raise TypeError(f"config type {type(config)} could not be recognized,"
                            " please use a dictionary or generic_cli.config.SessionConfig")

        service_name = service_name or self.service_name
        host = host or self.host
        prefix = (prefix
                  if prefix is None
                  else self.prefix)
        self._static: bool  #  If the host is present as an initialization parameter
                            #  the Client is not going to resolve the service's host
                            #  but rather always use the passed host
        if not host:
            self._static = False
            if not service_name and not env:
                raise TypeError("In auto-resolve mode both 'service_name' and 'env' must be provided")
            log.info('Running in auto-resolve mode')
        else:
            self._static = True
            log.info('Running in static mode with host: %r', host)
        self.__resolving = False
        self.__resolved: asyncio.Event
        self._host = host
        self._service_name = service_name
        self._prefix = prefix
        self.env = env
        self.config = session_config
        self.retriable_issue = return_from_signal(retry(**self.config.retry_policy,
                                                        retry=retry_if_exception_type(ShouldRetry),
                                                        sleep=asyncio.sleep)(self._retriable_issue))
        self._session = Session()
        try:
            self.exceptions = exceptions or self.exceptions
        except AttributeError:
            self.exceptions = {}

    async def __aenter__(self) -> 'AutoResolveClient':
        await self.open()
        return self

    async def open(self) -> None:
        '''Asynchroneously initialize Client'''
        try:
            await self.get_host()
        except:
            await self.close()
            raise

    async def __aexit__(self, exc_type: Type[Exception], exc: Exception, tb: TracebackType) -> None:
        await self.close()

    async def close(self) -> None:
        '''Close underlying async connections'''
        await self._session.close()


    def register_exception_cls(self, name: str, cls: Type[Exception]) -> None:
        '''Registers an exception class to be used on appropriate error responses'''
        self.exceptions[name] = cls

    async def get_host(self) -> str:
        '''
        Returns host url
        In the case host was passed as an argument to constructor it's going to be returned
        In the case it wasn't - it's going to be auto-resolved based on 'service_name' and 'env'
        '''
        if self._static:
            return cast(str, self._host)
        if self._host is not None:
            return self._host
        await self.resolve_host()
        return cast(str, self._host)

    async def resolve_host(self) -> None:
        '''
        Uses CrossRoads service discovery to determine
        corresponding service's host and saves it to self._host
        '''
        if self.__resolving:
            await self._wait_for_host_resolution()
            return
        self.__resolving = True
        self.__resolved = asyncio.Event()
        async with CrossRoads(self.env) as crossroads:
            host = await crossroads.get(self._service_name)
            log.info("Resolved %s's host to %r [name=%r env=%r]",
                     self.__class__.__name__,
                     host,
                     self._service_name,
                     self.env)
            self._host = host
            self.__resolving = False
            self.__resolved.set()

    async def _wait_for_host_resolution(self) -> None:
        await self.__resolved.wait()

    async def get_base_url(self) -> str:
        '''Returns client's base url'''
        host = await self.get_host()
        return f'{host}{self._prefix}'

    def _check_status(self, response: Response) -> None:
        str_status = str(response.status)
        retry_codes = self.config.retry_codes
        if (str_status in retry_codes
                or f'{str_status[:2]}x' in retry_codes
                or f'{str_status[:1]}xx' in retry_codes):
            raise ShouldRetry(response)

    @contextmanager
    def _check_error(self) -> None:
        try:
            yield
        except self.config.retry_errors as ex:
            raise ShouldRetry(ex)

    async def _retriable_issue(self, method: str, path: str, **kw) -> Response:
        '''Manages all request dispatches'''
        base_url = await self.get_base_url()
        url = f'{base_url}{path}'
        log.info('[%r] Getting url %r', datetime.now().strftime('%H:%M:%S.%f'), url)
        with self._check_error():
            res = await self._session.request(method, url, **kw)
            self._check_status(res)
        return res

    @asynccontextmanager
    async def issue(self, method: str, path: str, **kw) -> AsyncIterator[Response]:
        async with await self.retriable_issue(method, path, **kw) as res:
            if res.status != 200:
                try:
                    payload = await res.json(loads=json.loads)
                    if (payload.get('status') == 'error'
                            and payload.get('cls') is not None):
                        cls = self.exceptions.get(payload.get('cls'))
                        if cls is not None:
                            raise cls(payload)
                except:
                    raise
            yield res

    @asynccontextmanager
    async def post(self, *a, **kw) -> AsyncIterator[Response]:
        '''Issues a post request'''
        async with self.issue('POST', *a, **kw) as res:
            yield res

    @asynccontextmanager
    async def get(self, *a, **kw) -> AsyncIterator[Response]:
        '''Issues a get request'''
        async with self.issue('GET', *a, **kw) as res:
            yield res

    @asynccontextmanager
    async def put(self, *a, **kw) -> AsyncIterator[Response]:
        '''Issues a put request'''
        async with self.issue('PUT', *a, **kw) as res:
            yield res

    @asynccontextmanager
    async def delete(self, *a, **kw) -> AsyncIterator[Response]:
        '''Issues a delete request'''
        async with self.issue('DELETE', *a, **kw) as res:
            yield res

    @asynccontextmanager
    async def head(self, *a, **kw) -> AsyncIterator[Response]:
        '''Issues a head request'''
        async with self.issue('HEAD', *a, **kw) as res:
            yield res

    def _get_cls_config(self) -> Dict[str, Any]:
        cfg: Dict[str, Any] = {}
        for config_field in self.__config_fields__:
            if hasattr(self.__class__, config_field):
                cfg[config_field] = getattr(self.__class__, config_field)
        return cfg
