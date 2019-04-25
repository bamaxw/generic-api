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
    def __init__(self, *a, name: str = 'GenericAPI', settings: Optional[Dict[str, Any]] = None, **kw) -> None:
        super().__init__(*a, **kw)
        self.name = name
        self._settings = settings or {}

    @classmethod
    async def init(cls, *a, **kw) -> 'API':
        '''Asynchroneously initializes aiohttp Application'''
        app = cls(*a, **kw)
        await app.setup()
        log.info('Application %r setup completed...', app.name)
        return app

    async def setup(self) -> None:
        self.setup_settings()
        self.setup_logging()
        log.info('Application settings: %s', self['settings'])
        self.setup_swagger()

    def setup_settings(self) -> None:
        '''
        Combine settings from different sources (init argument, os.env and defaults)
        and attach them to self
        '''
        env = Env(
            PORT=dict(default=5000, cast=str),
            LOG_LEVEL=dict(default='WARNING', cast=str),
            LOGGING_CONF=dict(default=None, cast=str),
            SWAGGER_FILE=dict(default='./api/config/swagger.yml', cast=str),
            SWAGGER_URL=dict(default='api/doc', cast=str),
            SWAGGER_ENABLED=dict(default=False, cast=bool),
            ENVIRONMENT=dict(cast=str)
        )
        self['settings'] = {
            'port': env('PORT'),
            'environment': env('ENVIRONMENT'),
            'log_level': env('LOG_LEVEL'),
            'logging_conf': env('LOGGING_CONF'),
            'swagger': {
                'enabled': env('SWAGGER_ENABLED'),
                'url': env('SWAGGER_URL'),
                'file': env('SWAGGER_FILE')
            }
        }
        self['settings'].update(self._settings)

    def setup_logging(self) -> None:
        '''
        Sets up logging using file specified in settings['logging_conf'] or env LOGGING_CONF
        and sets the root log-level to LOG_LEVEL (default=WARNING)
        '''
        if self['settings']['logging_conf']:
            logging.config.fileConfig(self['settings']['logging_conf'])
            logging.getLogger().setLevel(self['settings']['log_level'])
        else:
            logging.basicConfig(level=self['settings']['log_level'])

    def setup_swagger(self) -> None:
        '''Setup swagger if its enabled'''
        if self['settings']['swagger']['enabled']:
            url = self['settings']['swagger']['url']
            file = self['settings']['swagger']['file']
            log.info('Setting up swagger from file %r [url: %r]', file, url)
            setup_swagger(self,
                          swagger_url=url,
                          swagger_from_file=file)
