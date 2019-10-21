from functools import wraps
from flask import request


def token_required_for_job_id(f):
    @wraps(f)
    def decorated(*args, **kwargs):

        print('MY FIRST DECORATOR!')
        print('kwargs: ', kwargs)
        id = kwargs.get('id')
        print('id: ', id)
        token = request.args.get('token')
        print('token: ', token)
        return f(*args, **kwargs)

    return decorated

