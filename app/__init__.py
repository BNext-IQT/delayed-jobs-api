"""
Entry file for the delayed jobs app
"""

from flask import Flask, Blueprint
from flask_restplus import Api

from app.namespaces.admin_auth.admin_auth_controller import API as job_admin_namespace
from app.namespaces.job_status.job_status_controller import API as job_status_namespace
from app.namespaces.job_submission.submit_test_job_controller import API as submit_test_job_namespace
from app.namespaces.job_submission.submit_similarity_controller import API as submit_similarity_search_namespace
from app.namespaces.job_submission.submit_substructure_controller import API as submit_substructure_search_namespace
from app.namespaces.job_submission.submit_connectivity_controller import API as submit_connectivity_search_namespace
from app.namespaces.job_submission.submit_blast_controller import API as submit_blast_search_namespace
from app.namespaces.job_submission.submit_download_controller import API as submit_download_namespace
from app.namespaces.job_statistics.record_search_controller import API as record_search_namespace
from app.namespaces.job_statistics.record_download_controller import API as record_download_namespace
from app.db import DB
from app.config import RUN_CONFIG
from app.config import RunEnvs


def create_app():
    """
    Creates the flask app
    :return: Delayed jobs flask app
    """

    flask_app = Flask(__name__)
    flask_app.config['SQLALCHEMY_DATABASE_URI'] = RUN_CONFIG.get('sql_alchemy').get('database_uri')
    flask_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = RUN_CONFIG.get('sql_alchemy').get('track_modifications')
    flask_app.config['SECRET_KEY'] = RUN_CONFIG.get('server_secret_key')

    set_up_app_logger(flask_app)

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

        blueprint = Blueprint('api', __name__, url_prefix=RUN_CONFIG.get('base_path'))
        api = Api(
            title='ChEMBL Interface Delayed Jobs',
            version='1.0',
            description='A microservice that runs delayed jobs for the ChEMBL interface. '
                        'For example generating a .csv file from elasticsearch',
            app=blueprint,
            authorizations=authorizations,
        )

        flask_app.register_blueprint(blueprint)

        for namespace in [job_admin_namespace, job_status_namespace, submit_test_job_namespace,
                          submit_similarity_search_namespace, submit_substructure_search_namespace,
                          submit_connectivity_search_namespace, submit_blast_search_namespace, record_search_namespace,
                          record_download_namespace, submit_download_namespace]:
            api.add_namespace(namespace)

        return flask_app

def set_up_app_logger(flask_app):
    """
    Sets up the logger for the app
    :param flask_app: flask app
    """

    print('LOGGING: ')
    flask_app.logger.setLevel(20)

    flask_app.logger.debug('this is a DEBUG message')
    flask_app.logger.info('this is an INFO message')
    flask_app.logger.warning('this is a WARNING message')
    flask_app.logger.error('this is an ERROR message')
    flask_app.logger.critical('this is a CRITICAL message')

if __name__ == '__main__':
    flask_app = create_app()
