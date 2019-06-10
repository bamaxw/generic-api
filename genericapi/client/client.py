from __future__ import annotations
from typing import Optional
import logging

from .engine import RequestEngine

log = logging.getLogger(__name__)


class Client(RequestEngine):
    __slots__ = RequestEngine.__slots__ + ('host',)
    host: Optional[str] = None
    def __init__(self, host: Optional[str] = None) -> None:
        host = host or self.host
        if not host:
            raise ValueError('no host specified')
        super().__init__(host)
