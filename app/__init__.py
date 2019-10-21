"""
Entry file for the delayed jobs app
"""
from flask import Flask
from flask_restplus import Api

from app.apis.job_status.job_status_controller import API as job_status_api
from app.apis.job_submission.submit_similarity_controller import API as similarity_api
from app.db import db
from app.config import RUN_CONFIG


def create_app():

    flask_app = Flask(__name__)
    flask_app.config['SQLALCHEMY_DATABASE_URI'] = RUN_CONFIG.get('sql_alchemy').get('database_uri')
    flask_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = RUN_CONFIG.get('sql_alchemy').get('track_modifications')
    flask_app.config['SERVER_SECRET_KEY'] = RUN_CONFIG.get('server_secret_key')

    with flask_app.app_context():
        db.init_app(flask_app)

        api = Api(
            title='ChEMBL Interface Delayed Jobs',
            version='1.0',
            description='A microservice that runs delayed jobs for the ChEMBL interface. '
                        'For example generating a .csv file from elasticsearch',
            app=flask_app)

        api.add_namespace(job_status_api)
        api.add_namespace(similarity_api)

        return flask_app


if __name__ == '__main__':
    create_app()
