"""
Entry file for the delayed jobs app
"""
from flask import Flask
from flask_cors import CORS

from app.config import RUN_CONFIG
from app.config import RunEnvs
from app.db import DB
from app.blueprints.swagger_description.swagger_description_blueprint import SWAGGER_BLUEPRINT
from app.blueprints.job_submission.controllers.job_submissions_controller import SUBMISSION_BLUEPRINT


def create_app():
    """
    Creates the flask app
    :return: Delayed jobs flask app
    """

    flask_app = Flask(__name__)
    flask_app.config['SQLALCHEMY_DATABASE_URI'] = RUN_CONFIG.get('sql_alchemy').get('database_uri')
    flask_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = RUN_CONFIG.get('sql_alchemy').get('track_modifications')
    flask_app.config['SECRET_KEY'] = RUN_CONFIG.get('server_secret_key')

    enable_cors = RUN_CONFIG.get('enable_cors', False)

    if enable_cors:
        CORS(flask_app)

    authorizations = {
        'jobKey': {
            'type': 'apiKey',
            'in': 'header',
            'name': 'X-Job-Key'
        },
        'adminKey': {
            'type': 'apiKey',
            'in': 'header',
            'name': 'X-Admin-Key'
        }
    }

    with flask_app.app_context():
        DB.init_app(flask_app)

        create_tables = RUN_CONFIG.get('sql_alchemy').get('create_tables', False)
        if create_tables:
            DB.create_all()

        base_path = RUN_CONFIG.get('base_path', '')

        flask_app.register_blueprint(SWAGGER_BLUEPRINT, url_prefix=f'{base_path}/swagger')
        flask_app.register_blueprint(SUBMISSION_BLUEPRINT, url_prefix=f'{base_path}/submit')

        return flask_app

if __name__ == '__main__':
    flask_app = create_app()
