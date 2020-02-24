"""
The blueprint used in job submission
"""
from flask import Blueprint, jsonify, request, abort

from app.blueprints.job_submission.services import job_submission_service
from app.blueprints.job_submission.controllers import marshmallow_schemas

SUBMISSION_BLUEPRINT = Blueprint('job_submission', __name__)

# ----------------------------------------------------------------------------------------------------------------------
# Generic submission function
# ----------------------------------------------------------------------------------------------------------------------
def submit_job(job_type, form_data, form_files, validation_schema):
    validation_errors = validation_schema().validate(form_data)
    if validation_errors:
        abort(400, str(validation_errors))

    response = job_submission_service.parse_args_and_submit_job(job_type, form_data, form_files)
    return jsonify(response)

# ----------------------------------------------------------------------------------------------------------------------
# Job submission endpoints
# ----------------------------------------------------------------------------------------------------------------------
@SUBMISSION_BLUEPRINT.route('/test_job', methods = ['POST'])
def submit_test_job():

    job_type = 'TEST'
    form_data = request.form
    form_files = request.files
    validation_schema = marshmallow_schemas.TestJobSchema
    return submit_job(job_type, form_data, form_files, validation_schema)

@SUBMISSION_BLUEPRINT.route('/mmv_job', methods = ['POST'])
def submit_mmv_job():

    job_type = 'MMV'
    form_data = request.form
    form_files = request.files
    validation_schema = marshmallow_schemas.MMVJobSchema
    return submit_job(job_type, form_data, form_files, validation_schema)