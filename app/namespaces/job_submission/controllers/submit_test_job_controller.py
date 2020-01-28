"""
Module that describes and handles the requests to submit a test job
"""
from flask import request
from flask_restx import Namespace, Resource, fields

from app.namespaces.job_submission.services import job_submission_service
from app.namespaces.job_submission.shared_marshalls import BASE_SUBMISSION_RESPONSE
from app.namespaces.models import delayed_job_models

API = Namespace('submit/test_job', description='Namespace to submit a test job')

TEST_JOB = API.model('TestJob', {
    'instruction': fields.String(description='How do you want the job to behave',
                                 required=True,
                                 example='RUN_NORMALLY',
                                 enum=['RUN_NORMALLY', 'FAIL']
                                 ),
    'seconds': fields.Integer(description='The amount of seconds that the job will run for',
                              required=True,
                              min=0,
                              example=1)
})

SUBMISSION_RESPONSE = API.inherit('SubmissionResponse', BASE_SUBMISSION_RESPONSE)


@API.route('/')
class SubmitTestJob(Resource):
    """
        Resource that handles test job submission requests
    """
    job_type = delayed_job_models.JobTypes.TEST

    @API.expect(TEST_JOB)
    @API.doc(body=TEST_JOB)
    @API.marshal_with(BASE_SUBMISSION_RESPONSE)
    def post(self):  # pylint: disable=no-self-use
        """
        Submits a job to the queue.
        :return: a json response with the result of the submission
        """
        print('submit test', request.json)
        response = job_submission_service.submit_job(self.job_type, request.json)
        return response
