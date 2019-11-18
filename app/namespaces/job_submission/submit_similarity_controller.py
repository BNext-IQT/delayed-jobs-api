from flask import request
from flask_restplus import Namespace, Resource, fields
from app.namespaces.job_submission.shared_marshalls import BASE_SUBMISSION_RESPONSE
from app.namespaces.models import delayed_job_models
from app.namespaces.job_submission import job_submission_service

API = Namespace('submit/similarity', description='Namespace to submit a similarity job')

SIMILARITY_JOB = API.model('SimilarityJob', {
    'structure': fields.String(description='The structure (SMILES) you want to search against',
                               required=True,
                               example='[H]C1(CCCN1C(=N)N)CC1=NC(=NO1)C1C=CC(=CC=1)NC1=NC(=CS1)C1C=CC(Br)=CC=1'),
    'threshold': fields.Integer(description='The threshold for the similarity search',
                                required=True,
                                min=70,
                                max=100,
                                example=90)
})

SUBMISSION_RESPONSE = API.inherit('SubmissionResponse', BASE_SUBMISSION_RESPONSE)


@API.route('/')
class SubmitSimilarityJob(Resource):
    """
        Resource that handles similarity search job submission requests
    """
    job_type = delayed_job_models.JobTypes.SIMILARITY

    @API.expect(SIMILARITY_JOB)
    @API.doc(body=SIMILARITY_JOB)
    @API.marshal_with(BASE_SUBMISSION_RESPONSE)
    def post(self):  # pylint: disable=no-self-use
        """
        Submits a job to the queue.
        :return: a json response with the result of the submission
        """

        json_data = request.json
        job_params = {
            **json_data,
            'search_type': str(self.job_type),
        }
        response = job_submission_service.submit_job(self.job_type, job_params)
        return response