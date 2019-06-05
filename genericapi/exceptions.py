from typing import Any, Dict


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
                                         **kw}
