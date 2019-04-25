'''
All classes extending aiohttp.web.Application
with simplified initialization and setup
'''
from typing import Any, Dict, Optional
import logging.config
import logging

from aiohttp_swagger import setup_swagger
from aiohttp.web import Application
from envparse import Env

log = logging.getLogger(__name__)


class API(Application):
    def __init__(self,
                 *a,
                 name: str = 'GenericAPI',
                 settings: Optional[Dict[str, Any]] = None,
                 envdefinition: Optional[Dict[str, Dict[str, Any]]] = None,
                 **kw) -> None:
        super().__init__(*a, **kw)
        self.name = name
        self.settings = settings or {}
        self.env = Env(
            **dict(
                dict(
                    PORT=dict(default=5000, cast=str),
                    LOG_LEVEL=dict(default='WARNING', cast=str),
                    LOGGING_CONF=dict(default=None, cast=str),
                    SWAGGER_FILE=dict(default='./api/config/swagger.yml', cast=str),
                    SWAGGER_URL=dict(default='api/doc', cast=str),
                    SWAGGER_ENABLED=dict(default=False, cast=bool),
                    ENVIRONMENT=dict(cast=str)
                ),
                **envdefinition or {}
            )
        )

    @classmethod
    async def init(cls, *a, **kw) -> 'API':
        '''Asynchroneously initializes aiohttp Application'''
        app = cls(*a, **kw)
        await app.setup()
        log.info('Application %r setup completed...', app.name)
        return app

    async def setup(self) -> None:
        self.setup_logging()
        self.setup_swagger()

    def config(self, key: str) -> Any:
        '''Retrieve key from config'''
        try:
            return self.settings[key]
        except KeyError:
            return self.env(key.upper())

    def setup_logging(self) -> None:
        '''
        Sets up logging using file specified in settings['logging_conf'] or env LOGGING_CONF
        and sets the root log-level to LOG_LEVEL (default=WARNING)
        '''
        if self.config('logging_conf'):
            logging.config.fileConfig(self.config('logging_conf'))
            logging.getLogger().setLevel(self.config('log_level'))
        else:
            logging.basicConfig(level=self.config('log_level'))

    def setup_swagger(self) -> None:
        '''Setup swagger if its enabled'''
        if self.config('swagger_enabled'):
            url = self.config('swagger_url')
            file = self.config('swagger_file')
            log.info('Setting up swagger from file %r [url: %r]', file, url)
            setup_swagger(self,
                          swagger_url=url,
                          swagger_from_file=file)
