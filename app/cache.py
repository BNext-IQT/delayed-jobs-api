"""
    Module that handles the connection with the cache
"""
from flask_caching import Cache

from app.config import RUN_CONFIG

CACHE = Cache(config=RUN_CONFIG['cache_config'])
