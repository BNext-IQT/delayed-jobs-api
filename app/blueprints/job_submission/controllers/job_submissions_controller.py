"""
The blueprint used in job submission
"""
from flask import Blueprint, jsonify, request

from app.blueprints.job_submission.services import job_submission_service
from app.blueprints.job_submission.controllers import marshmallow_schemas
from app.request_validation.decorators import validate_form_with

SUBMISSION_BLUEPRINT = Blueprint('job_submission', __name__)

# ----------------------------------------------------------------------------------------------------------------------
# Generic submission function
# ----------------------------------------------------------------------------------------------------------------------
def submit_job(job_type, form_data, form_files):
    response = job_submission_service.parse_args_and_submit_job(job_type, form_data, form_files)
    return jsonify(response)

# ----------------------------------------------------------------------------------------------------------------------
# Job submission endpoints
# ----------------------------------------------------------------------------------------------------------------------
@SUBMISSION_BLUEPRINT.route('/test_job', methods = ['POST'])
@validate_form_with(marshmallow_schemas.TestJobSchema)
def submit_test_job():

    job_type = 'TEST'
    form_data = request.form
    form_files = request.files
    return submit_job(job_type, form_data, form_files)

@SUBMISSION_BLUEPRINT.route('/mmv_job', methods = ['POST'])
@validate_form_with(marshmallow_schemas.MMVJobSchema)
def submit_mmv_job():

    job_type = 'MMV'
    form_data = request.form
    form_files = request.files
    return submit_job(job_type, form_data, form_files)