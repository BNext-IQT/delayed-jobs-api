"""
Module that handles decorators used in request validation
"""
from flask import request, abort
from functools import wraps

def validate_with(validation_schema):

    def wrap(func):

        @wraps(func)
        def wrapped_func(*args, **kwargs):

            form_data = request.form
            validation_errors = validation_schema().validate(form_data)
            if validation_errors:
                abort(400, str(validation_errors))

            return func(*args, **kwargs)

        return wrapped_func

    return wrap