try:
    import ujson as autojson
except ModuleNotFoundError:
    try:
        import simplejson as autojson
    except ModuleNotFoundError:
        import autojson
