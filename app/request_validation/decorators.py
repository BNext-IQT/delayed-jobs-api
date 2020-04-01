"""
Module that handles decorators used in request validation
"""
from flask import request, abort
from functools import wraps

def validate_form_with(validation_schema):

    def wrap(func):

        @wraps(func)
        def wrapped_func(*args, **kwargs):

            validation_errors = validation_schema().validate(request.form)
            if validation_errors:
                abort(400, str(validation_errors))

            return func(*args, **kwargs)

        return wrapped_func

    return wrap


def validate_url_params_with(validation_schema):

    def wrap(func):

        @wraps(func)
        def wrapped_func(*args, **kwargs):

            validation_errors = validation_schema().validate(kwargs)
            if validation_errors:
                abort(400, str(validation_errors))

            return func(*args, **kwargs)

        return wrapped_func

    return wrap