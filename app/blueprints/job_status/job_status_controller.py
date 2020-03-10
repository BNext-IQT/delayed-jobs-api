"""
The blueprint used for handling the jobs status
"""
from flask import Blueprint, jsonify, abort, request

from app.blueprints.job_status import job_status_service
from app.authorisation.decorators import token_required_for_job_id

JOB_STATUS_BLUEPRINT = Blueprint('job_status', __name__)

@JOB_STATUS_BLUEPRINT.route('/<job_id>', methods = ['GET'])
def get_job_status(job_id):

    try:
        return jsonify(job_status_service.get_job_status(job_id))
    except job_status_service.JobNotFoundError:
        abort(404)

@JOB_STATUS_BLUEPRINT.route('/<job_id>', methods = ['PATCH'])
@token_required_for_job_id
def update_job_progress(job_id):

    try:
        progress = int(request.form.get('progress'))
        status_log = request.form.get('status_log')
        return jsonify(job_status_service.update_job_progress(job_id, progress, status_log))
    except job_status_service.JobNotFoundError:
        abort(500, 'Job was deleted...')