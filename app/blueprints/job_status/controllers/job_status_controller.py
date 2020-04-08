"""
The blueprint used for handling the jobs status
"""
from flask import Blueprint, jsonify, abort, request

from app.authorisation.decorators import token_required_for_job_id
from app.blueprints.job_status.services import job_status_service
from app.blueprints.job_status.controllers import marshmallow_schemas
from app.request_validation.decorators import validate_form_with, validate_url_params_with
import app.app_logging as app_logging

JOB_STATUS_BLUEPRINT = Blueprint('job_status', __name__)

@JOB_STATUS_BLUEPRINT.route('/<job_id>', methods = ['GET'])
@validate_url_params_with(marshmallow_schemas.JobStatus)
def get_job_status(job_id):

    try:
        return jsonify(job_status_service.get_job_status(job_id))
    except job_status_service.JobNotFoundError:
        abort(404)

@JOB_STATUS_BLUEPRINT.route('/<job_id>', methods = ['PATCH'])
@token_required_for_job_id
@validate_url_params_with(marshmallow_schemas.JobStatus)
@validate_form_with(marshmallow_schemas.JobStatusUpdate)
def update_job_progress(job_id):

    try:
        progress = int(request.form.get('progress'))
        status_log = request.form.get('status_log')
        status_description = request.form.get('status_description')
        return jsonify(job_status_service.update_job_progress(job_id, progress, status_log, status_description))
    except job_status_service.JobNotFoundError:
        abort(500, 'Job was deleted...')