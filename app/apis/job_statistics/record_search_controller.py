from flask_restplus import Namespace, Resource, fields
from app.apis.models import delayed_job_models

API = Namespace('record/search', description='Requests to record statistics of a search')

SEARCH_RECORD = API.model('SearchRecord', {
    'total_items': fields.Integer(required=True, description='The type of search performed', min=0),
    'file_size': fields.Integer(required=True, description='The final size of the results file in bytes', min=0),
})


@API.route('/<id>')
@API.param('id', 'The job identifier')
@API.response(404, 'Job not found')
class SearchRecord(Resource):
    """
        Resource that handles requests regarding recording search statistics
    """

    @API.doc(body=SEARCH_RECORD)
    @API.marshal_with(SEARCH_RECORD)
    def post(self, id):
        """
        Records statistics of a search with the data provided
        :return: a json response with the result of the submission
        """

        print('SAVE FOR: ', id)
        return {
            'total_items': 0
        }