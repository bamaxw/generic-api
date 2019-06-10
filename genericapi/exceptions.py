from __future__ import annotations
from typing import Any, Dict
from functools import wraps
from pprint import pformat
import importlib
import logging

from aiohttp.web import json_response, Response
from aiohttp import ClientResponse

from .types import AsyncRouteHandler
from .json import autojson

log = logging.getLogger(__name__)


def with_exception_serializer(handler: AsyncRouteHandler) -> AsyncRouteHandler:
    '''
    Wraps a handler function and listens to any errors surfacing
    if an error gets caught by the wrapper -- it gets serialized and returned to the user
    '''
    @wraps(handler)
    async def _wrapper(*a, **kw) -> Response:
        try:
            return await handler(*a, **kw)
        except Exception as exc:  #  pylint: disable=broad-except
            log.exception('exception caught -- serializing')
            return SerializableException.get_response(exc)
    return _wrapper


async def from_error_res(res: ClientResponse, blame: str = 'server') -> Exception:
    '''Turns a serializable-error response into a serializable error'''
    try:
        payload = await res.json(loads=autojson.loads)
    except ValueError:
        log.exception('Received non-autojson error response:\n%s', await res.text())
    return SerializableException.deserialize_exc(payload, status=res.status)


class NotAnError(TypeError):
    '''
    Raised when a response that is not an error
    is being deserialized
    '''


class SerializableException(Exception):
    '''
    Exception that can be json serialized and sent to another application
    As a http response
    '''
    _http_status: int
    exc_args: list = []
    exc_kwargs: Dict[str, Any] = {}
    def __new__(cls, *a, **kw) -> SerializableException:
        instance = super().__new__(cls, *a, **kw)
        instance.exc_args = list(a)
        instance.exc_kwargs = dict(kw)
        return instance

    def __init__(self, message: str, code: int = 0, status: str = 'error') -> None:
        super().__init__(message)
        self.http_status = code or self._http_status
        self.response_status = status

    @classmethod
    def get_response(cls, exc: Exception) -> Response:
        '''Turns an error into a response'''
        payload: Dict[str, Any] = {'status': 'error',
                                   'exc': cls.serialize_exc(exc),
                                   'message': 'an error has been raised'}
        status = 500
        if isinstance(exc, cls):
            payload['status'] = exc.response_status
            payload['message'] = payload['exc']['message']
            payload['exc']['args'] = exc.exc_args
            payload['exc']['kwargs'] = exc.exc_kwargs
            status = exc.http_status
        else:
            payload['exc']['args'] = [str(exc)]
        return json_response(payload, status=status, dumps=autojson.dumps)

    @staticmethod
    def serialize_exc(exc: Exception) -> Dict[str, str]:
        '''Serializes any exception'''
        return {'class': exc.__class__.__qualname__,
                'module': exc.__class__.__module__,
                'message': str(exc)}

    @staticmethod
    def deserialize_exc(exc_payload: Dict[str, Any], status: int) -> Exception:
        if exc_payload.get('status') != 'error':
            raise NotAnError()
        exc = exc_payload.get('exc')
        if exc is None:
            raise ValueError(f'received an error response that is not deserializable!\n{pformat(exc_payload)}!')
        exc_module = importlib.import_module(exc.pop('module'))
        exc_class = getattr(exc_module, exc.pop('class'))
        return exc_class(*exc.get('args') or (), **exc.get('kwargs') or {})
