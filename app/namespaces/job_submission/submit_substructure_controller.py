"""
Module that describes and handles the requests concerned with the substructure search
"""
from flask import request
from flask_restplus import Namespace, Resource, fields

from app.namespaces.job_submission.shared_marshalls import BASE_SUBMISSION_RESPONSE
from app.namespaces.models import delayed_job_models
from app.namespaces.job_submission import job_submission_service

API = Namespace('submit/substructure', description='Namespace to submit a substructure job')

SUBSTRUCTURE_JOB = API.model('SubstructureJob', {
    'structure': fields.String(description='The structure (SMILES) you want to search against',
                               required=True,
                               example='CC(=O)Oc1ccccc1C(=O)O'),
})

SUBMISSION_RESPONSE = API.inherit('SubmissionResponse', BASE_SUBMISSION_RESPONSE)


@API.route('/')
class SubmitConnectivityJob(Resource):
    """
        Resource that handles substructure search job submission requests
    """
    job_type = delayed_job_models.JobTypes.SUBSTRUCTURE

    @API.expect(SUBSTRUCTURE_JOB)
    @API.doc(body=SUBSTRUCTURE_JOB)
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
