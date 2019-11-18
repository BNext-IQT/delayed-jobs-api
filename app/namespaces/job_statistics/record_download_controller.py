"""
Module that describes and handles the requests concerned with recording the downloads
"""
from flask import abort, request
from flask_restplus import Namespace, Resource, fields

from app.namespaces.job_statistics import record_statistics_service
from app.authorisation.decorators import token_required_for_job_id

# pylint: disable=no-self-use,redefined-builtin,invalid-name
API = Namespace('record/download', description='Requests to record statistics of a download')

DOWNLOAD_RECORD = API.model('DownloadRecord', {
    'total_items': fields.Integer(required=True, description='The type of search performed', min=0),
    'file_size': fields.Integer(required=True, description='The final size of the results file in bytes', min=0),
    'es_index': fields.String(required=True, description='The es index used in the download'),
    'desired_format': fields.String(required=True, description='The file format of the generated download'),
})

FULL_STATISTICS = API.inherit('FullDownloadRecord', DOWNLOAD_RECORD, {
    'time_taken': fields.Integer(required=True, description='The time the job took to finish', min=0),
    'request_date': fields.Float(required=True, description='The time (POSIX timestamp) at what the job started', min=0)
})


@API.route('/<id>')
@API.param('id', 'The job identifier')
@API.response(404, 'Job not found')
@API.response(412, 'Job must be finished before saving statistics')
class DownloadRecord(Resource):
    """
        Resource that handles requests regarding recording download statistics
    """

    @API.doc(security='jobKey', body=DOWNLOAD_RECORD)
    @API.marshal_with(FULL_STATISTICS)
    @token_required_for_job_id
    def post(self, id):
        """
        Records statistics of a download with the data provided
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
