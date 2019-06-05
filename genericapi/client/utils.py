'''Utility functions and classes for core generic-cli'''
from typing import Any, Awaitable, Callable, cast, Dict, Tuple, TypeVar, Union
from functools import wraps
import inspect
import logging
import time

log = logging.getLogger(__name__)
T = TypeVar('T')
AsyncMethod = Callable[[Any], Awaitable[T]]
AsyncFunc = Callable[[], Awaitable[T]]
CacheKey = Union[AsyncFunc, Tuple[object, AsyncMethod]]
AsyncCallable = Union[AsyncMethod, AsyncFunc]


def minutes(mins: float) -> float:
    '''Returns amount of seconds in that many minutes'''
    return mins * 60


def cache_for(seconds: float) -> 'CacheFor':
    '''Same as CacheFor()'''
    return CacheFor(seconds)


class CacheFor:
    '''
    Caches function response for the amount of seconds
    specified in timeout argument passed to the class constructor
    '''
    _func_cache: Dict[CacheKey, Any] = {}
    _func_timestamps: Dict[CacheKey, float] = {}
    def __init__(self, timeout: float) -> None:
        self.timeout = timeout

    def __call__(self, func: AsyncCallable) -> AsyncCallable:
        sig = inspect.signature(func)
        params = sig.parameters
        if len(params) == 1 and 'self' in params:
            return self._decorate_method(cast(AsyncMethod, func))
        if not params:
            return self._decorate_func(cast(AsyncFunc, func))
        raise TypeError('CacheFor can be called on a method or function with no arguments only!'
                        f' Detected signature: {str(sig)}')

    def _decorate_func(self, func: AsyncFunc[T]) -> AsyncFunc[T]:
        @wraps(func)
        async def _func_wrapper(no_cache: bool = False) -> T:
            next_call_ts = self._func_timestamps.get(func, 0)
            if no_cache or next_call_ts <= time.time():
                self._func_cache[func] = await func()
                self._func_timestamps[func] = time.time() + self.timeout
            return self._func_cache[func]
        return _func_wrapper

    def _decorate_method(self, func: AsyncMethod[T]) -> AsyncMethod[T]:
        @wraps(func)
        async def _method_wrapper(self, no_cache: bool = False) -> T:
            key = (self, func)
            next_call_ts = self._func_timestamps.get(key, 0)
            if no_cache or next_call_ts <= time.time():
                self._func_cache[key] = await func(self)
                self._func_timestamps[key] = time.time() + self.timeout
            return self._func_cache[key]
        return _method_wrapper
