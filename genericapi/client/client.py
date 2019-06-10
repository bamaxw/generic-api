from __future__ import annotations
from typing import Optional
import logging

from .engine import RequestEngine

log = logging.getLogger(__name__)


class Client(RequestEngine):
    # Client allows some attributes to be set in a declarative way
    # like so
    # Client attributes
    __slots__ = RequestEngine.__slots__ + ('service_name', 'prefix', 'host', 'env')
    https: bool = False
    host: Optional[str] = None
    service_name: Optional[str] = None
    prefix: str = ''

    def __init__(self,
                 env: Optional[str] = None,
                 *,
                 service_name: Optional[str] = None,
                 prefix: str = '',
                 host: Optional[str] = None,
                 https: Optional[bool] = None) -> None:
        if https is None:
            https = self.https
        if service_name is None:
            service_name = self.service_name
        if host is None:
            host = self.host
        if host is None:
            if service_name is None or env is None:
                raise TypeError("a client with not host must have both 'service_name' and 'env'")
            if https:
                host = 'https://'
            else:
                host = 'http://'
            host += f'{service_name}-{env}.inyourarea.co.uk'
        if prefix is None:
            prefix = self.prefix
        baseurl = host + prefix
        super().__init__(baseurl)
        self.host = host
        self.service_name = service_name
        self.prefix = prefix
        self.env = env
