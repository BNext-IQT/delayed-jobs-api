from flask import Flask
from flask_restplus import Api, Resource

flask_app = Flask(__name__)
app = Api(app=flask_app)

name_space = app.namespace('delayed_jobs', description='Delayed Jobs for ChEMBL')


@name_space.route('/sumbit')
class SumbitJob(Resource):

    def post(self):
        return {
            "status": "A new job has been submitted!"
        }


@name_space.route('/status')
class JobStatus(Resource):
    def get(self):
        return {
            "status": "The job is running!"
        }
