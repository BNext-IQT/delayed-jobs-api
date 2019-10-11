"""
Entry file for the delayed jobs app
"""
from flask import Flask
from flask_restplus import Api
from app.apis.job_status_api import API as job_status_api
from app.apis.similarity_api import API as similarity_api

FLASK_APP = Flask(__name__)
API = Api(
    title='ChEMBL Interface Delayed Jobs',
    version='1.0',
    description='A microservice that runs delayed jobs for the ChEMBL interface. '
                'For example generating a .csv file from elasticsearch',
    app=FLASK_APP)

API.add_namespace(job_status_api)
API.add_namespace(similarity_api)