"""
Blueprint in charge of sending the swagger configuration in json format.
"""
from flask import Blueprint

SWAGGER_BLUEPRINT = Blueprint('swagger', __name__)

@SWAGGER_BLUEPRINT.route('/swagger.json')
def get_json():
    from flask import jsonify
    return jsonify({'hello': 'world'})
