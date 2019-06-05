try:
    import ujson as json
except ModuleNotFoundError:
    try:
        import simplejson as json
    except ModuleNotFoundError:
        import json
