"""
This Module receives the requests for the custom statistics
"""
from flask import Blueprint, jsonify

from app.blueprints.custom_statistics.controllers import marshmallow_schemas
from app.request_validation.decorators import validate_form_with, validate_url_params_with
from app.authorisation.decorators import token_required_for_job_id

CUSTOM_STATISTICS_BLUEPRINT = Blueprint('custom_statistics', __name__)

@CUSTOM_STATISTICS_BLUEPRINT.route('/submit_statistics/test_job/<job_id>', methods = ['POST'])
@token_required_for_job_id
@validate_url_params_with(marshmallow_schemas.JobID)
@validate_form_with(marshmallow_schemas.TestJobStatistics)
def submit_custom_statistics_test_job(job_id):
    print('SUBMIT CUSTOM STATS!')
    return jsonify({'operation_result': 'Statistics successfully saved!'})