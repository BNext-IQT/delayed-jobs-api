from flask import abort, request
from flask_restplus import Namespace, Resource, fields

from app.apis.models import delayed_job_models

API = Namespace('status', description='Requests related to Job Status')

MODIFIABLE_STATUS = API.model('ModifiableStatus', {
    'status': fields.String(required=True, description='The status of the job ',
                            enum=[str(possible_status) for possible_status in delayed_job_models.JobStatuses]),
    'status_comment': fields.String(required=True, description='A comment on the status of the job'),
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
    'expires': fields.String(required=True, description='The date at which the job results will expire'),
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
        job = delayed_job_models.DelayedJob.query.filter_by(id=id).first()
        if job is None:
            abort(400)
        else:
            return job.public_dict()

    @API.marshal_with(MODIFIABLE_STATUS)
    def patch(self, id):
        """
            Updates a job with the data provided
            :param id:
            :return:
        """
        job = delayed_job_models.DelayedJob.query.filter_by(id=id).first()
        if job is None:
            abort(400)
        else:
            for key in request.values.keys():
                new_value = request.values.get(key)
                if new_value is not None:
                    setattr(job, key, new_value)

        return job.public_dict()
