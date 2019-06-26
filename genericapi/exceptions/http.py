from typing import Any, Mapping, Optional, Union

import aiohttp.web

from ..json import autojson

JSONValue = Union[str, int, float, bool, dict, list, tuple, None]


class JSONResponseMixin(aiohttp.web.HTTPException):
    '''A HTTPException mixin that makes all respones uniformly return json'''
    def __init__(
            self,
            msg: str,
            *,
            status: str,
            blame: str = 'Server',
            headers: Optional[Mapping[str, Any]] = None,
            reason: Optional[str] = None,
            **params
    ) -> None:
        payload = {'Status': status,
                   'Message': msg,
                   'Blame': blame,
                   **params}
        super().__init__(text=autojson.dumps(payload),
                         headers=headers,
                         reason=reason,
                         content_type='application/json')


class HTTPError(JSONResponseMixin):
    def __init__(
            self,
            msg: str,
            *,
            headers: Optional[Mapping[str, Any]] = None,
            reason: Optional[str] = None,
            **params
    ) -> None:
        super().__init__(msg,
                         status='Error',
                         headers=headers,
                         reason=reason,
                         **params)
        # Add error message to the python repr of the error
        self.args = tuple(list(self.args)
                          + [msg]
                          + [f'{k}={v}'
                             for k, v in params.items()])


#  4xx
class HTTPBadRequest(HTTPError, aiohttp.web.HTTPBadRequest):
    '''BadRequest 400'''


class HTTPNotFound(HTTPError, aiohttp.web.HTTPNotFound):
    '''NotFound 404'''


class HTTPConflict(HTTPError, aiohttp.web.HTTPConflict):
    '''Conflict 409'''


class HTTPGone(HTTPError, aiohttp.web.HTTPGone):
    '''Gone 410'''

class HTTPTooManyRequests(HTTPError, aiohttp.web.HTTPTooManyRequests):
    '''TooManyRequests 429'''

class HTTPFailedDependency(HTTPError, aiohttp.web.HTTPFailedDependency):
    '''FailedDependency 424'''


#  2xx
class HTTPOk(aiohttp.web.HTTPOk):
    '''OK 200'''
    def __init__(
            self,
            payload: JSONValue,
            *,
            headers: Optional[Mapping[str, Any]] = None,
            reason: Optional[str] = None
    ) -> None:
        super().__init__(text=autojson.dumps(payload),
                         headers=headers,
                         reason=reason,
                         content_type='application/json')


#  5xx
class HTTPServiceUnavailable(HTTPError, aiohttp.web.HTTPServiceUnavailable):
    '''ServiceUnavailable 503'''


class HTTPInternalServerError(HTTPError, aiohttp.web.HTTPInternalServerError):
    '''InternalServerError 500'''
