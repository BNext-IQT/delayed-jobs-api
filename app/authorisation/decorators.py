"""
Module that handles decorators used in the authorisation of different endpoints.
"""
from functools import wraps
from flask import request, jsonify

import jwt

from app.config import RUN_CONFIG


def token_required_for_job_id(func):
    """
    Checks the token provided, the job_id in the token must match the job id that the function aims receives as
    parameter. Makes the function return a 403 http error if the token is missing, 401 if is invalid.
    :param func: function to decorate
    :return: decorated function
    """
    @wraps(func)
    def decorated(*args, **kwargs):

        job_id = kwargs.get('job_id')
        token = request.headers.get('X-Job-Key')
        key = RUN_CONFIG.get('server_secret_key')

        if token is None:
            return jsonify({'message': 'Token is missing'}), 403

        try:
            token_data = jwt.decode(token, key, algorithms=['HS256'])
            authorised_id = token_data.get('job_id')
            if authorised_id != job_id:
                return jsonify({'message': f'You are not authorised modify the job {id}'}), 401
        except:
            return jsonify({'message': 'Token is invalid'}), 401

        return func(*args, **kwargs)

    return decorated


def admin_token_required(func):
    """
    Checks that a valid admin token is provided.
    parameter. Makes the function return a 403 http error if the token is missing, 401 if is invalid.
    :param func: function to decorate
    :return: decorated function
    """

    @wraps(func)
    def decorated(*args, **kwargs):

        token = request.headers.get('X-Admin-Key')
        key = RUN_CONFIG.get('server_secret_key')

        if token is None:
            return jsonify({'message': 'Token is missing'}), 403

        try:
            token_data = jwt.decode(token, key, algorithms=['HS256'])
            username = token_data.get('username')
            if username != RUN_CONFIG.get('admin_username'):
                return jsonify({'message': f'You are not authorised for this operation'}), 401

        except:
            return jsonify({'message': 'Token is invalid'}), 401

        return func(*args, **kwargs)

    return decorated
