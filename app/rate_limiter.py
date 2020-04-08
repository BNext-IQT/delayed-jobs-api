"""
Module that defines the instance of the rate limiter
"""
from flask_limiter import Limiter
from flask_limiter.util import get_ipaddr

PER_SECOND = 2

RATE_LIMITER = Limiter(
    key_func=get_ipaddr,
    default_limits=[f'{PER_SECOND*60*60*24} per day', f'{PER_SECOND*60*60} per hour']
)