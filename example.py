import asyncio

from genericapi import API

async def main():
    '''Initializes sample generic api'''
    app = await API.init(name='MaxAPI')
    return app


if __name__ == '__main__':
    app = asyncio.run(main())
