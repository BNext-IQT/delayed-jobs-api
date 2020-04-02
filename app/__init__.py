"""
Entry file for the delayed jobs app
"""
from flask import Flask
from flask_cors import CORS

from app.blueprints.admin.controllers.admin_tasks_controller import ADMIN_TASKS_BLUEPRINT
from app.blueprints.admin.controllers.authorisation_controller import ADMIN_AUTH_BLUEPRINT
from app.blueprints.job_status.controllers.job_status_controller import JOB_STATUS_BLUEPRINT
from app.blueprints.job_submission.controllers.job_submissions_controller import SUBMISSION_BLUEPRINT
from app.blueprints.job_submission.services import job_submission_service
from app.blueprints.swagger_description.swagger_description_blueprint import SWAGGER_BLUEPRINT
from app.config import RUN_CONFIG
from app.config import RunEnvs
from app.db import DB
from app.models import delayed_job_models
from app.cache import CACHE

def create_app():
    """
    Creates the flask app
    :return: Delayed jobs flask app
    """

    base_path = RUN_CONFIG.get('base_path', '')
    outputs_base_path = RUN_CONFIG.get('outputs_base_path', 'outputs')
    flask_app = Flask(__name__,
                      static_url_path=f'{base_path}/{outputs_base_path}',
                      static_folder=job_submission_service.JOBS_OUTPUT_DIR)

    # flask_app.config['SERVER_NAME'] = RUN_CONFIG.get('server_public_host')
    flask_app.config['SQLALCHEMY_DATABASE_URI'] = RUN_CONFIG.get('sql_alchemy').get('database_uri')
    flask_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = RUN_CONFIG.get('sql_alchemy').get('track_modifications')
    flask_app.config['SECRET_KEY'] = RUN_CONFIG.get('server_secret_key')

    enable_cors = RUN_CONFIG.get('enable_cors', False)

    if enable_cors:
        CORS(flask_app)

    with flask_app.app_context():
        DB.init_app(flask_app)
        CACHE.init_app(flask_app)

        create_tables = RUN_CONFIG.get('sql_alchemy').get('create_tables', False)
        if create_tables:
            DB.create_all()

        generate_default_config = RUN_CONFIG.get('generate_default_config', False)
        if generate_default_config:
            delayed_job_models.generate_default_job_configs()

        flask_app.register_blueprint(SWAGGER_BLUEPRINT, url_prefix=f'{base_path}/swagger')
        flask_app.register_blueprint(SUBMISSION_BLUEPRINT, url_prefix=f'{base_path}/submit')
        flask_app.register_blueprint(JOB_STATUS_BLUEPRINT, url_prefix=f'{base_path}/status')
        flask_app.register_blueprint(ADMIN_AUTH_BLUEPRINT, url_prefix=f'{base_path}/admin')
        flask_app.register_blueprint(ADMIN_TASKS_BLUEPRINT, url_prefix=f'{base_path}/admin')

        return flask_app

if __name__ == '__main__':
    flask_app = create_app()
