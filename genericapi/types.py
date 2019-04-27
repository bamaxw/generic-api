from typing import Any, Awaitable, Callable, Dict, Response

AsyncRouteHandler = Callable[..., Awaitable[Response]]
RawCorsConfig = Dict[str, Dict[str, Any]]
