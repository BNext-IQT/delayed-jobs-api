from flask_restplus import Namespace, Resource, fields

API = Namespace('status', description='Requests related to Job Status')

STATUS = API.model('Status', {
    'id': fields.String(required=True, description='The job identifier'),
    'status': fields.String(required=True, description='The status of the job ')
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
        return {
            'id': id,
            'status': 'The job is running!'
        }