"""
Module that describes and handles the requests concerned with recording the search events
"""
from flask import abort, request
from flask_restx import Namespace, Resource, fields

from app.namespaces.job_statistics import record_statistics_service
from app.authorisation.decorators import token_required_for_job_id
from app.namespaces.models import delayed_job_models

# pylint: disable=redefined-builtin,invalid-name,no-self-use
API = Namespace('record/search', description='Requests to record statistics of a search')

SEARCH_RECORD = API.model('SearchRecord', {
    'total_items': fields.Integer(required=True, description='The type of search performed', min=0),
    'file_size': fields.Integer(required=True, description='The final size of the results file in bytes', min=0),
})

FULL_STATISTICS = API.inherit('FullSearchRecord', SEARCH_RECORD, {
    'time_taken': fields.Integer(required=True, description='The time the job took to finish', min=0),
    'search_type': fields.String(required=True, description='The type of the job ',
                                 enum=[str(possible_type) for possible_type in delayed_job_models.JobTypes]),
    'request_date': fields.Float(required=True, description='The time (POSIX timestamp) at what the job started', min=0)
})


@API.route('/<id>')
@API.param('id', 'The job identifier')
@API.response(404, 'Job not found')
@API.response(412, 'Job must be finished before saving statistics')
class SearchRecord(Resource):
    """
        Resource that handles requests regarding recording search statistics
    """

    @API.doc(security='jobKey', body=SEARCH_RECORD)
    @API.marshal_with(FULL_STATISTICS)
    @token_required_for_job_id
    def post(self, id):
        """
        Records statistics of a search with the data provided
        :return: a json response with the result of the submission
        """

        statistics = {}  # this is to avoid using custom data structures i.e CombinedMultiDict
        for key in request.values.keys():
            new_value = request.values.get(key)
            statistics[key] = new_value

        try:
            return record_statistics_service.save_statistics_for_job(id, statistics)
        except record_statistics_service.JobNotFoundError:
            abort(404)
        except record_statistics_service.JobNotFinishedError:
            abort(412)
