"""
Blueprint for authorisation endpoints for the administration of the system
"""
from flask import Blueprint, jsonify, request, make_response

from app.blueprints.admin.services import authorisation_service

ADMIN_AUTH_BLUEPRINT = Blueprint('admin_auth', __name__)

@ADMIN_AUTH_BLUEPRINT.route('/login', methods = ['GET'])
def login():

    auth = request.authorization

    try:
        token = authorisation_service.get_admin_token(auth.username, auth.password)
        return jsonify({'token': token})
    except authorisation_service.InvalidCredentialsError as error:
        return make_response(str(error), 401, {'WWW-Authenticate': 'Basic realm="Login Required'})