"""
Blueprint for authorisation endpoints for the administration of the system
"""
from flask import Blueprint, jsonify, request, make_response

from app.blueprints.admin.services import authorisation_service
from app.rate_limiter import RATE_LIMITER
from app.config import RUN_CONFIG

ADMIN_AUTH_BLUEPRINT = Blueprint('admin_auth', __name__)

@ADMIN_AUTH_BLUEPRINT.route('/login', methods = ['GET'])
@RATE_LIMITER.limit(RUN_CONFIG.get('rate_limit').get('rates').get('admin_login'))
def login():

    auth = request.authorization

    if auth is None:
        return make_response('No login credentials were provided!', 400,
                             {'WWW-Authenticate': 'Basic realm="Login Required'})

    try:
        token = authorisation_service.get_admin_token(auth.username, auth.password)
        return jsonify({'token': token})
    except authorisation_service.InvalidCredentialsError as error:
        return make_response(str(error), 401, {'WWW-Authenticate': 'Basic realm="Login Required'})