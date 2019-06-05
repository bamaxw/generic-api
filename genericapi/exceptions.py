from typing import Any, Dict
from functools import wraps

from aiohttp.web import Response

from .types import AsyncRouteHandler
from .json import json


def catch_serializable_exceptions(handler: AsyncRouteHandler) -> AsyncRouteHandler:
    @wraps(handler)
    async def _wrapper(*a, **kw) -> Response:
        try:
            return await handler(*a, **kw)
        except SerializableException as ex:
            return Response(text=json.dumps(ex._payload),  #  pylint: disable=protected-access
                            status=ex._http_status,  #  pylint: disable=protected-access
                            content_type='application/json')
    return _wrapper


class SerializableException(Exception):
    '''
    Exception that can be json serialized and sent to another application
    As a http response
    '''
    _http_status: int
    _cls: str
    def __init__(self, msg: str, code: int = 0, status: str = 'error', **kw) -> None:
        super().__init__(msg)
        self._http_status = code or self._http_status
        try:
            self._cls = self._cls
        except AttributeError:
            self._cls = self.__class__.__name__
        self._payload: Dict[str, Any] = {'status': status,
                                         'message': msg,
                                         'cls': self._cls,
                                         **kw}
