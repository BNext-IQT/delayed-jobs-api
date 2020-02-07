"""
Module that describes and handles the requests to submit a test job
"""
from flask_restx import Resource, Namespace, reqparse
import werkzeug

from app.namespaces.job_submission.services import job_submission_service
from app.namespaces.job_submission.shared_marshalls import BASE_SUBMISSION_RESPONSE
from app.namespaces.models import delayed_job_models

API = Namespace('submit/test_job', description='Namespace to submit a test job')

TEST_JOB_PARSER = reqparse.RequestParser()
TEST_JOB_PARSER.add_argument('input1',
                             type=werkzeug.datastructures.FileStorage,
                             location='files',
                             required=True,
                             help='Input File 1')

TEST_JOB_PARSER.add_argument('input2',
                             type=werkzeug.datastructures.FileStorage,
                             location='files',
                             required=True,
                             help='Input File 2')

TEST_JOB_PARSER.add_argument('instruction',
                             choices=('RUN_NORMALLY', 'FAIL'),
                             required=True,
                             help='How do you want the job to behave')

TEST_JOB_PARSER.add_argument('seconds',
                             choices=tuple(i for i in range(1, 301)),
                             type=int,
                             required=True,
                             help='How many seconds you want the job to run for')

TEST_JOB_PARSER.add_argument('api_url',
                             required=True,
                             help='The url on an API to test a call to in the job',
                             default='https://www.ebi.ac.uk/chembl/api/data/similarity/CN1C(=O)C=C(c2cccc(Cl)c2)c3cc(ccc13)[C@@](N)(c4ccc(Cl)cc4)c5cncn5C/80.json')

SUBMISSION_RESPONSE = API.inherit('SubmissionResponse', BASE_SUBMISSION_RESPONSE)


@API.route('/')
class SubmitTestJob(Resource):
    """
        Resource that handles test job submission requests
    """
    job_type = delayed_job_models.JobTypes.TEST
    docker_image_url = 'docker://dockerhub.ebi.ac.uk/chembl/chembl/delayed-jobs/test-job:latest'

    @API.expect(TEST_JOB_PARSER)
    # @API.doc(body=TEST_JOB)
    @API.marshal_with(BASE_SUBMISSION_RESPONSE)
    def post(self):  # pylint: disable=no-self-use
        """
        Submits a job to the queue.
        :return: a json response with the result of the submission
        """
        args = TEST_JOB_PARSER.parse_args()
        response = job_submission_service.parse_args_and_submit_job(self.job_type, args, self.docker_image_url)
        return response
