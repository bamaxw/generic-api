from typing import Any, Dict
from functools import wraps

from aiohttp.web import json_response, Response

from .types import AsyncRouteHandler
from .json import json


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
            return SerializableException.get_response(exc)
    return _wrapper


class SerializableException(Exception):
    '''
    Exception that can be json serialized and sent to another application
    As a http response
    '''
    _http_status: int
    def __init__(self, msg: str, code: int = 0, status: str = 'error', **params) -> None:
        super().__init__(msg)
        self.http_status = code or self._http_status
        self.response_status = status
        self.response_params = params

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
            payload['exc']['params'] = exc.response_params
            status = exc.http_status
        return json_response(payload, status=status, dumps=json.dumps)

    @staticmethod
    def serialize_exc(exc: Exception) -> Dict[str, str]:
        '''Serializes any exception'''
        return {'class': exc.__class__.__qualname__,
                'module': exc.__class__.__module__,
                'message': str(exc)}
