"""
This module checks the login info provided and returns a token if the credentials are valid
"""
from app.config import RUN_CONFIG
from app.config import verify_secret
from app.authorisation import token_generator

class InvalidCredentialsError(Exception):
    """Base class for exceptions in this module."""

def get_admin_token(username, password):

    username_must_be = RUN_CONFIG.get('admin_username')
    username_is_correct = username_must_be == username
    password_is_correct = verify_secret('admin_password', password)

    if username_is_correct and password_is_correct:
        return token_generator.generate_admin_token()
    else:
        raise InvalidCredentialsError('Could not verify the credentials provided!')