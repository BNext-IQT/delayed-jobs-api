from flask import abort, request
from flask_restplus import Namespace, Resource, fields
from app.apis.models import delayed_job_models
from app.apis.job_status import job_status_service
from app.authorisation.decorators import token_required_for_job_id
import werkzeug
from flask_restplus import reqparse

API = Namespace('status', description='Requests related to Job Status')

MODIFIABLE_STATUS = API.model('ModifiableStatus', {
    'status': fields.String(required=True, description='The status of the job ',
                            enum=[str(possible_status) for possible_status in delayed_job_models.JobStatuses]),
    'status_comment': fields.String(required=True, description='A comment on the status of the job'),
    'log': fields.String(required=True, description='The log of messages from the job'),
    'progress': fields.String(required=True, description='The progress percentage of the job'),
    'output_file_path': fields.String(required=True, description='The path where the result file is located'),
    'api_initial_url': fields.String(required=True, description='The initial URL of the API calls'),
})


PUBLIC_STATUS = API.inherit('Status', MODIFIABLE_STATUS, {
    'id': fields.String(required=True, description='The job identifier'),
    'type': fields.String(required=True, description='The type of the job ',
                          enum=[str(possible_type) for possible_type in delayed_job_models.JobTypes]),
    'created_at': fields.String(required=True, description='The time at which the job was created'),
    'started_at': fields.String(required=True, description='The time at which the job started to run'),
    'finished_at': fields.String(required=True, description='The time at which the job finished'),
    'raw_params': fields.String(required=True, description='The stringified version of the parameters'),
    'expires_at': fields.String(required=True, description='The date at which the job results will expire'),
    'timezone': fields.String(required=True, description='The timezome where the job ran'),

})


@API.route('/<id>')
@API.param('id', 'The job identifier')
@API.response(404, 'Job not found')
class JobStatus(Resource):
    """
        Resource that handles job status requests
    """

    @API.marshal_with(PUBLIC_STATUS)
    def get(self, id):  # pylint: disable=no-self-use
        """
        Returns the status of a job
        :return: a json response with the current job status
        """
        try:
            return job_status_service.get_job_status(id)
        except job_status_service.JobNotFoundError:
            abort(404)

    @API.marshal_with(MODIFIABLE_STATUS)
    @API.doc(security='jobKey', body=MODIFIABLE_STATUS)
    @token_required_for_job_id
    def patch(self, id):
        """
            Updates a job with the data provided
            :param id:
            :return:
        """
        new_data = {}  # this is to avoid using custom data structures i.e CombinedMultiDict
        for key in request.values.keys():
            new_value = request.values.get(key)
            new_data[key] = new_value

        try:
            return job_status_service.update_job_status(id, new_data)
        except job_status_service.JobNotFoundError:
            abort(404)


RESULT_FILE_OPERATION = API.model('Result File Operation', {
    'result': fields.String(description='The result of the operation')
})

FILE_TO_UPLOAD = reqparse.RequestParser()
FILE_TO_UPLOAD.add_argument('results_file',
                            type=werkzeug.datastructures.FileStorage,
                            location='files',
                            required=True,
                            help='Results file of the job')


@API.route('/<id>/results_file')
@API.param('id', 'The job identifier')
@API.response(404, 'Job not found')
class JobResultsFileUpload(Resource):
    """
    Resource to handle the upload of a results file for a job
    """
    @API.marshal_with(RESULT_FILE_OPERATION)
    @API.expect(FILE_TO_UPLOAD)
    def post(self, id):
        """
        Handles the upload of a results file for a job
        :param id: job id
        :return:
        """
        print('FILE RECEIVED!')
        print('RECEIVING FILE!', request.files['results_file'])
        return {
            'result': 'file received!'
        }
