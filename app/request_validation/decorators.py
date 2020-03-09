"""
Module that handles decorators used in request validation
"""
from flask import request, abort
from functools import wraps

def validate_with(validation_schema, validate_from_func_args=False):

    def wrap(func):

        @wraps(func)
        def wrapped_func(*args, **kwargs):

            print('VALIDATING')
            print(args)
            print(kwargs)

            if validate_from_func_args:
                obj_to_validate = request.form
            else:
                obj_to_validate = kwargs

            validation_errors = validation_schema().validate(obj_to_validate)
            if validation_errors:
                abort(400, str(validation_errors))

            return func(*args, **kwargs)

        return wrapped_func

    return wrap