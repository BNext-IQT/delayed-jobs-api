"""
Blueprint for authorisation endpoints for the administration of the system
"""
from flask import Blueprint, jsonify

ADMIN_AUTH_BLUEPRINT = Blueprint('admin_auth', __name__)

@ADMIN_AUTH_BLUEPRINT.route('/login', methods = ['GET'])
def login():
    print('LOGGING IN!')
    return jsonify({'token': 'kkk'})