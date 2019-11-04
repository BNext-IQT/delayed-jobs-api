from flask import abort, request, make_response, jsonify
from flask_restplus import Namespace, Resource, fields
from app.authorisation import token_generator
from app.config import verify_secret

API = Namespace('admin_auth', description='Request to login and get a token for the admin user')


@API.route('/login')
class AdminLogin(Resource):
    """
        Resource that handles admin login requests
    """
    def get(self):
        """
            If the login and password are correct, returns a token authorising the admin
            :return: a Json Web Token authorising the admin user
        """
        auth = request.authorization
        if auth is not None and verify_secret('admin_password', auth.password):
            admin_token = token_generator.generate_admin_token()
            return jsonify({'token': admin_token})

        return make_response('Could not verify username and password', 401,
                             {'WWW-Authenticate': 'Basic real="Login Required'})
