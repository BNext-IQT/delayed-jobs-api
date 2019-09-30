"""
Entry file for the delayed jobs app
"""
from flask import Flask
from flask_restplus import Api, Resource
import job_submitter

FLASK_APP = Flask(__name__)
APP = Api(app=FLASK_APP)

NAME_SPACE = APP.namespace('delayed_jobs', description='Delayed Jobs for ChEMBL')


@NAME_SPACE.route('/sumbit')
class SubmitJob(Resource):
    """
    Resource that handles job submission requests
    """
    # pylint: disable=no-self-use
    def post(self):
        """
        Submits a job to the queue.
        :return: a json response with the result of the submission
        """
        job_submitter.submit_job()
        return {
            "status": "A new job has been submitted!"
        }


@NAME_SPACE.route('/status')
class JobStatus(Resource):
    """
        Resource that handles job status requests
    """

    # pylint: disable=no-self-use
    def get(self):
        """
        Returns the status of a job
        :return: a json response with the current job status
        """
        return {
            "status": "The job is running!"
        }
