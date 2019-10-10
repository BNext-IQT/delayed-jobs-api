"""
Entry file for the delayed jobs app
"""
from flask import Flask
from flask_restplus import Api
from app.apis.job_status_api import API as job_status_api

FLASK_APP = Flask(__name__)
API = Api(
    title='ChEMBL Interface Delayed Jobs',
    version='1.0',
    description='A microservice that runs delayed jobs for the ChEMBL interface. '
                'For example generating a .csv file from elasticsearch',
    app=FLASK_APP)

API.add_namespace(job_status_api)



# @NAME_SPACE.route('/submit/similarity')
# class SubmitSimilarityJob(Resource):
#     """
#         Resource that handles similarity search job submission requests
#     """
#     job_type = DelayedJob.JobTypes.SIMILARITY
#     fields = API.model('SubmitSimilarityJob', {
#         'structure': fields.String(description='The structure (SMILES) you want to search against',
#                                    required=True,
#                                    example='[H]C1(CCCN1C(=N)N)CC1=NC(=NO1)C1C=CC(=CC=1)NC1=NC(=CS1)C1C=CC(Br)=CC=1'),
#         'threshold': fields.Integer(description='The threshold for the similarity search',
#                                     required=True,
#                                     min=70,
#                                     max=100,
#                                     example=90)
#     })
#     @API.doc(body=fields)
#     def post(self): # pylint: disable=no-self-use
#         """
#         Submits a job to the queue.
#         :return: a json response with the result of the submission
#         """
#
#         response = job_submitter.submit_job(self.job_type, API.payload)
#         return response
#
# # pylint: disable=fixme
# # TODO
# @NAME_SPACE.route('/sumbit/substructure')
# class SubmitSubstructureJob(Resource):
#     """
#         Resource that handles substructure search job submission requests
#     """
#     job_type = DelayedJob.JobTypes.SUBSTRUCTURE
#
# # TODO
# @NAME_SPACE.route('/sumbit/connectivity')
# class SubmitConnectivityJob(Resource):
#     """
#         Resource that handles connectivity search job submission requests
#     """
#     job_type = DelayedJob.JobTypes.CONNECTIVITY
#
# # TODO
# @NAME_SPACE.route('/sumbit/blast')
# class SubmitBlastJob(Resource):
#     """
#         Resource that handles BLAST search job submission requests
#     """
#     job_type = DelayedJob.JobTypes.BLAST
#
# # TODO
# @NAME_SPACE.route('/sumbit/download')
# class SubmitDownloadJob(Resource):
#     """
#         Resource that handles Download job submission requests
#     """
#     job_type = DelayedJob.JobTypes.DOWNLOAD
