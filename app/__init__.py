"""
Entry file for the delayed jobs app
"""
from flask import Flask
from flask_restplus import Api
from app.models.db import db
from app.apis.job_status_api import API as job_status_api
from app.apis.similarity_api import API as similarity_api


def create_app():

    flask_app = Flask(__name__)
    flask_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    flask_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

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
