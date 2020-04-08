"""
Module that defines the instance of the rate limiter
"""
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

RATE_LIMITER = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)