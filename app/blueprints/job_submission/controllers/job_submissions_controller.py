"""
The blueprint used in job submission
"""
from flask import Blueprint, jsonify, request

from app.models import delayed_job_models
from app.blueprints.job_submission.services import job_submission_service

SUBMISSION_BLUEPRINT = Blueprint('job_submission', __name__)

@SUBMISSION_BLUEPRINT.route('/test_job', methods = ['POST'])
def submit_test_job():

    job_type = delayed_job_models.JobTypes.TEST
    docker_image_url = 'docker://dockerhub.ebi.ac.uk/chembl/chembl/delayed-jobs/test-job:cfc42a35-final'

    response = job_submission_service.parse_args_and_submit_job(job_type, request.form, request.files, docker_image_url)
    return jsonify(response)