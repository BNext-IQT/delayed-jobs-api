"""
Module that defines the instance of the rate limiter
"""
from flask_limiter import Limiter
from flask_limiter.util import get_ipaddr

PER_SECOND = 0.5

RATE_LIMITER = Limiter(
    key_func=get_ipaddr,
    default_limits=['1 per day']
)