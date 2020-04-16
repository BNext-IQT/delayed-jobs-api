"""
The blueprint used in job submission
"""
from flask import Blueprint, jsonify, request, abort

from app.blueprints.job_submission.services import job_submission_service
from app.blueprints.job_submission.controllers import marshmallow_schemas
from app.request_validation.decorators import validate_form_with
from app.rate_limiter import RATE_LIMITER
from app.config import RUN_CONFIG


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
@RATE_LIMITER.limit(RUN_CONFIG.get('rate_limit').get('rates').get('job_submission'))
def submit_test_job():

    job_type = 'TEST'
    form_data = request.form
    form_files = request.files
    return submit_job(job_type, form_data, form_files)

@SUBMISSION_BLUEPRINT.route('/mmv_job', methods = ['POST'])
@validate_form_with(marshmallow_schemas.MMVJobSchema)
@RATE_LIMITER.limit(RUN_CONFIG.get('rate_limit').get('rates').get('job_submission'))
def submit_mmv_job():

    job_type = 'MMV'
    form_data = request.form
    form_files = request.files
    return submit_job(job_type, form_data, form_files)

@SUBMISSION_BLUEPRINT.route('/structure_search_job', methods = ['POST'])
@validate_form_with(marshmallow_schemas.StructureSearchJobSchema)
@RATE_LIMITER.limit(RUN_CONFIG.get('rate_limit').get('rates').get('job_submission'))
def submit_structure_search_job():

    job_type = 'STRUCTURE_SEARCH'
    form_data = request.form
    form_files = request.files

    # one small additional validation
    search_type = form_data.get('search_type')
    threshold = form_data.get('threshold')
    if search_type == 'SIMILARITY' and threshold is None:
        abort(400, 'When the search type is similarity, you must provide a threshold!')

    return submit_job(job_type, form_data, form_files)