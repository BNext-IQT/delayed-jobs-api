"""
Module that describes and handles the requests concerned with the downloads
"""
from flask import request
from flask_restplus import Namespace, Resource, fields

from app.namespaces.job_submission.shared_marshalls import BASE_SUBMISSION_RESPONSE
from app.namespaces.models import delayed_job_models
from app.namespaces.job_submission import job_submission_service

API = Namespace('submit/download', description='Namespace to submit a download job')

DOWNLOAD_JOB = API.model('DownloadJob', {
    'index_name': fields.String(description='The index against you want to make the download',
                                required=True, example='chembl_molecule'),
    'query': fields.String(description='Query to execute against the index to get the items',
                           required=True, example='{"bool":{"must":[{"query_string":'
                                                  '{"analyze_wildcard":true,"query":"*"}}],"filter":[[{"bool":'
                                                  '{"should":[{"term":{"molecule_type":"Antibody"}}]}}]]}}'),
    'format': fields.String(description='Format of the download (SDF is available for the chembl_molecule index only)',
                            required=True, example='SVG', enum=['CSV', 'TSV', 'SDF']),
    'download_columns_group': fields.String(description='Group that summarises and describes the columns that you want '
                                                        'to download. See for example: https://www.ebi.ac.uk/chembl/'
                                                        'glados_api/shared/properties_configuration/group/'
                                                        'chembl_molecule/download/', example='download'),
    'context_id': fields.String(description='Id of the results of another job to join to the download. '
                                            'Useful to join structure or sequence search results.'),
})

SUBMISSION_RESPONSE = API.inherit('SubmissionResponse', BASE_SUBMISSION_RESPONSE)


@API.route('/')
class SubmitConnectivityJob(Resource):
    """
        Resource that handles download job submission requests
    """
    job_type = delayed_job_models.JobTypes.DOWNLOAD

    @API.expect(DOWNLOAD_JOB)
    @API.doc(body=DOWNLOAD_JOB)
    @API.marshal_with(SUBMISSION_RESPONSE)
    def post(self):  # pylint: disable=no-self-use
        """
        Submits a job to the queue.
        :return: a json response with the result of the submission
        """

        json_data = request.json
        response = job_submission_service.submit_job(self.job_type, json_data)
        return response
