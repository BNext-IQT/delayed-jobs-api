"""
Module that describes and handles the requests concerned with performing admin tasks
"""
from flask import request, make_response, jsonify
from flask_restx import Namespace, Resource, fields

from app.authorisation import token_generator
from app.config import verify_secret
from app.config import RUN_CONFIG
from app.authorisation.decorators import admin_token_required
from app.namespaces.models import delayed_job_models

API = Namespace('admin', description='Request to login and get a token for the admin user')

OPERATION_RESULT = API.model('OperationResult', {
    'result': fields.String(description='The result of the admin operation.'),
})


# pylint: disable=no-self-use,broad-except
@API.route('/login')
class AdminLogin(Resource):
    """
        Resource that handles admin login requests.
    """
    def get(self):
        """
            If the login and password are correct, returns a token authorising the admin
            :return: a Json Web Token authorising the admin user
        """
        auth = request.authorization
        if auth is not None:

            if auth.username == RUN_CONFIG.get('admin_username') and verify_secret('admin_password', auth.password):
                admin_token = token_generator.generate_admin_token()
                return jsonify({'token': admin_token})

        return make_response('Could not verify username and password', 401,
                             {'WWW-Authenticate': 'Basic realm="Login Required'})


@API.route('/delete_expired')
class DeleteExpired(Resource):
    """
       Resource that triggers the deletion of the expired jobs. Admin token is required.
    """

    @API.marshal_with(OPERATION_RESULT)
    @API.doc(security='adminKey')
    @admin_token_required
    def get(self):
        """
        Deletes the expired jobs in the system.
        :return: a summary of the result of the operation
        """

        try:

            num_deleted = delayed_job_models.delete_all_expired_jobs()
            return {
                'result': f'Successfully deleted {num_deleted} expired jobs.'
            }

        except Exception as exception:

            return {
                'result': f'There was an error: {str(exception)}'
            }
