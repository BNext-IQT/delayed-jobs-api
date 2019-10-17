from flask import abort
from flask_restplus import Namespace, Resource, fields

from app.apis.models import delayed_job_models

API = Namespace('status', description='Requests related to Job Status')

STATUS = API.model('Status', {
    'id': fields.String(required=True, description='The job identifier'),
    'type': fields.String(required=True, description='The type of the job '),
    'status': fields.String(required=True, description='The status of the job '),
    'status_comment': fields.String(required=True, description='A comment on the status of the job'),
    'progress': fields.String(required=True, description='The progress percentage of the job'),
    'created_at': fields.String(required=True, description='The time at which the job was created'),
    'started_at': fields.String(required=True, description='The time at which the job started to run'),
    'finished_at': fields.String(required=True, description='The time at which the job finished'),
    'output_file_path': fields.String(required=True, description='The path where the result file is located'),
    'raw_params': fields.String(required=True, description='The stringified version of the parameters'),
    'expires': fields.String(required=True, description='The date at which the job results will expire'),
    'api_initial_url': fields.String(required=True, description='The initial URL of the API calls'),
    'timezone': fields.String(required=True, description='The timezome where the job ran'),

})


@API.route('/<id>')
@API.param('id', 'The job identifier')
@API.response(404, 'Job not found')
class JobStatus(Resource):
    """
        Resource that handles job status requests
    """

    @API.marshal_with(STATUS)
    def get(self, id): # pylint: disable=no-self-use
        """
        Returns the status of a job
        :return: a json response with the current job status
        """
        job = delayed_job_models.DelayedJob.query.filter_by(id=id).first()
        if job is None:
            abort(400)
        else:
            return job.public_dict()