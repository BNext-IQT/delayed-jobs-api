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

    def get(self): # pylint: disable=no-self-use
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
        Resource that handles similarity search job submission requests
    """
    job_type = DelayedJob.SIMILARITY
    fields = APP.model('SubmitSimilarityJob', {
        'structure': fields.String(description='The structure (SMILES) you want to search against',
                                   required=True,
                                   example='[H]C1(CCCN1C(=N)N)CC1=NC(=NO1)C1C=CC(=CC=1)NC1=NC(=CS1)C1C=CC(Br)=CC=1'),
        'threshold': fields.Integer(description='The threshold for the similarity search',
                                    required=True,
                                    min=70,
                                    max=100,
                                    example=90)
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

# pylint: disable=fixme
# TODO
@NAME_SPACE.route('/sumbit/substructure')
class SubmitSubstructureJob(Resource):
    """
        Resource that handles substructure search job submission requests
    """
    job_type = DelayedJob.SUBSTRUCTURE

# TODO
@NAME_SPACE.route('/sumbit/connectivity')
class SubmitConnectivityJob(Resource):
    """
        Resource that handles connectivity search job submission requests
    """
    job_type = DelayedJob.CONNECTIVITY

# TODO
@NAME_SPACE.route('/sumbit/blast')
class SubmitBlastJob(Resource):
    """
        Resource that handles BLAST search job submission requests
    """
    job_type = DelayedJob.BLAST

# TODO
@NAME_SPACE.route('/sumbit/download')
class SubmitDownloadJob(Resource):
    """
        Resource that handles Download job submission requests
    """
    job_type = DelayedJob.DOWNLOAD
