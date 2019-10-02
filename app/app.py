"""
Entry file for the delayed jobs app
"""
from flask import Flask
from flask_restplus import Api, Resource, fields
from .models import DelayedJob

FLASK_APP = Flask(__name__)
APP = Api(app=FLASK_APP)

NAME_SPACE = APP.namespace('delayed_jobs', description='Delayed Jobs for ChEMBL')


@APP.doc(params={'id': 'The ID of the job that you want to request the status for'})
@NAME_SPACE.route('/status')
class JobStatus(Resource):
    """
        Resource that handles job status requests
    """

    # pylint: disable=no-self-use
    def get(self):
        """
        Returns the status of a job
        :return: a json response with the current job status
        """
        return {
            "status": "The job is running!"
        }


@NAME_SPACE.route('/submit/similarity')
class SubmitSimilarityJob(Resource):
    """
        Resource that handles similarity job submission requests
    """
    job_type = DelayedJob.SIMILARITY
    fields = APP.model('SubmitSimilarityJob', {
        'structure': fields.String(description='The structure (SMILES) you want to search against',
                                   required=True,
                                   example='hola'),
        'threshold': fields.Integer(required=True, min=70, max=100, example=90)
    })
    @APP.doc(body=fields)
    def post(self): # pylint: disable=no-self-use
        """
        Submits a job to the queue.
        :return: a json response with the result of the submission
        """
        return {
            "status": f'A new {self.job_type.lower()} job has been submitted!'
        }



@NAME_SPACE.route('/sumbit/substructure')
class SubmitSubstructureJob(Resource):
    job_type = DelayedJob.SUBSTRUCTURE
    pass


@NAME_SPACE.route('/sumbit/connectivity')
class SubmitConnectivityJob(Resource):
    job_type = DelayedJob.CONNECTIVITY
    pass


@NAME_SPACE.route('/sumbit/blast')
class SubmitBlastJob(Resource):
    job_type = DelayedJob.BLAST
    pass


@NAME_SPACE.route('/sumbit/download')
class SubmitDownloadJob(Resource):
    job_type = DelayedJob.DOWNLOAD
    pass
