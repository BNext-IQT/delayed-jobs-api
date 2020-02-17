"""
The blueprint used in job submission
"""
from flask import Blueprint, jsonify, request

from app.models import delayed_job_models
from app.blueprints.job_submission.services import job_submission_service

SUBMISSION_BLUEPRINT = Blueprint('job_submission', __name__)

@SUBMISSION_BLUEPRINT.route('/test_job', methods = ['POST'])
def submit_test_job():

    job_type = 'TEST'
    response = job_submission_service.parse_args_and_submit_job(job_type, request.form, request.files)
    return jsonify(response)