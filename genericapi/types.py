from typing import Any, Awaitable, Callable, Dict

from aiohttp.web import Response

AsyncRouteHandler = Callable[..., Awaitable[Response]]
RawCorsConfig = Dict[str, Dict[str, Any]]
