"""
    Module that handles the connection with the cache
"""
from flask_caching import Cache
CACHE = Cache(config={'CACHE_TYPE': 'simple'})