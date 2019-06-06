from typing import Dict, List, Optional

from aiohttp_cors import setup as setup_cors, ResourceOptions as CorsResourceOptions
from aiohttp_cors.cors_config import CorsConfig
from aiohttp.web_urldispatcher import ResourceRoute
from aiohttp.web import Application

from ..exceptions import with_exception_serializer
from ..types import AsyncRouteHandler, RawCorsConfig

DEFAULT_CORS_CONFIG = {
    '*': dict(
        expose_headers='*',
        allow_headers='*',
        allow_methods='*',
        allow_credentials=True
    )
}


def compile_cors_config(cors_config: RawCorsConfig) -> Dict[str, CorsResourceOptions]:
    '''Compile cors config in a dictionary form to cors config accepted by cors.add'''
    return {cors_path: CorsResourceOptions(**cors_path_config)
            for cors_path, cors_path_config in cors_config.items()}


class RouteManager:
    '''Utility class helping with registering routes'''
    def __init__(self, app: Application, *, root: str = '', cors: RawCorsConfig = DEFAULT_CORS_CONFIG) -> None:
        self.app = app
        self.root = root
        self.cors = setup_cors(app, defaults=compile_cors_config(cors))

    def _get_cors_config(self,
                         cors: Optional[RawCorsConfig],
                         no_cors: bool) -> Optional[CorsConfig]:
        if no_cors:
            return None
        if cors:
            return compile_cors_config(cors)
        return self.cors

    def add_route(self,
                  *,
                  method: str,
                  path: str,
                  handler: AsyncRouteHandler,
                  name: Optional[str] = None,
                  cors: Optional[RawCorsConfig] = None,
                  no_cors: bool = False) -> ResourceRoute:
        '''Add a route to application router
           Arguments:
             method  -- route method (GET, POST, ...)
             path    -- route path (/healthcheck etc)
             handler -- route handler
             name    -- route name
             cors    -- pass cors config to override the default cors'''
        route = self.app.router.add_route(method=method,
                                          path=f'{self.root}{path}',
                                          handler=with_exception_serializer(handler),
                                          name=name)
        _cors = self._get_cors_config(cors, no_cors)
        if _cors:
            route = _cors.add(route)
        return route

    def add_routes(self, routes: List[dict]) -> None:
        '''
        Add batch of routes to application router
        Each route should be a dictionary containing all required arguments
        to method RouteManager.add_route
        '''
        for route in routes:
            self.add_route(**route)
