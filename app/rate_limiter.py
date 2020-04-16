"""
Module that defines the instance of the rate limiter
"""
from flask_limiter import Limiter
from flask_limiter.util import get_ipaddr

from app.config import RUN_CONFIG

RATE_LIMITER = Limiter(
    key_func=get_ipaddr,
    default_limits=[RUN_CONFIG.get('rate_limit').get('rates').get('default_for_all_routes')],
    storage_uri=RUN_CONFIG.get('rate_limit').get('storage_url')
)