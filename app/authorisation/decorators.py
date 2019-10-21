from functools import wraps
from flask import request, jsonify
from app.config import RUN_CONFIG
import jwt


def token_required_for_job_id(f):
    @wraps(f)
    def decorated(*args, **kwargs):

        id = kwargs.get('id')
        token = request.headers.get('X-Job-Key')
        key = RUN_CONFIG.get('server_secret_key')

        if token is None:
            return jsonify({'message': 'Token is missing'}), 403

        try:
            token_data = jwt.decode(token, key, algorithms=['HS256'])
        except:
            return jsonify({'message': 'Token is invalid'}), 401

        authorised_id = token_data.get('job_id')
        if authorised_id != id:
            return jsonify({'message': f'You are not authorised modify the job {id}'}), 401

        return f(*args, **kwargs)

    return decorated

