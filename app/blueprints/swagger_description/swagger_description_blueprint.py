"""
Blueprint in charge of sending the swagger configuration in json format.
"""
from pathlib import Path

from flask import Blueprint, jsonify
import yaml

from app.config import RUN_CONFIG

SWAGGER_BLUEPRINT = Blueprint('swagger', __name__)

@SWAGGER_BLUEPRINT.route('/swagger.json')
def get_json():

    yaml_file_path = Path(Path().absolute()).joinpath('app', 'swagger', 'swagger.yaml')

    with open(yaml_file_path, 'r') as stream:
        swagger_desc = yaml.safe_load(stream)
        swagger_desc['host'] = RUN_CONFIG.get('server_public_host')
        swagger_desc['basePath'] = RUN_CONFIG.get('base_path')
        return jsonify(swagger_desc)
