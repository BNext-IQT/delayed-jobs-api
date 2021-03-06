"""
Module that handles the generation of tokens for the app
"""
import datetime

import jwt

from app.config import RUN_CONFIG


JOB_TOKEN_HOURS_TO_LIVE = 24
ADMIN_TOKEN_HOURS_TO_LIVE = 1


def generate_job_token(job_id):
    """
    Generates a token that is valid ONLY to modify the job whose id is set as parameter.
    :param job_id: id of the job for which the toke will be valid
    :return: JWT token
    """

    token_data = {
        'job_id': job_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=JOB_TOKEN_HOURS_TO_LIVE)
    }

    key = RUN_CONFIG.get('server_secret_key')
    token = jwt.encode(token_data, key).decode('UTF-8')

    return token


def generate_admin_token():
    """
    Generates a token that can be used to be authorised for admin tasks
    :return: JWT token
    """

    token_data = {
        'username': RUN_CONFIG.get('admin_username'),
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=ADMIN_TOKEN_HOURS_TO_LIVE)
    }

    key = RUN_CONFIG.get('server_secret_key')
    token = jwt.encode(token_data, key).decode('UTF-8')

    return token
