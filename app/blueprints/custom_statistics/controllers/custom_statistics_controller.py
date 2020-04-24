"""
This Module receives the requests for the custom statistics
"""
from flask import Blueprint, jsonify, request, abort

from app.blueprints.custom_statistics.controllers import marshmallow_schemas
from app.request_validation.decorators import validate_form_with, validate_url_params_with
from app.authorisation.decorators import token_required_for_job_id
from app.blueprints.custom_statistics.services import custom_statistics_service

CUSTOM_STATISTICS_BLUEPRINT = Blueprint('custom_statistics', __name__)

@CUSTOM_STATISTICS_BLUEPRINT.route('/submit_statistics/test_job/<job_id>', methods = ['POST'])
# @token_required_for_job_id
@validate_url_params_with(marshmallow_schemas.JobID)
@validate_form_with(marshmallow_schemas.TestJobStatistics)
def submit_custom_statistics_test_job(job_id):

    try:
        duration = request.form.get('duration')
        return jsonify(custom_statistics_service.save_custom_statistics_test_job(job_id, duration))
    except custom_statistics_service.JobNotFoundError:
        abort(404, f'Job with id {job_id} does not exist!')