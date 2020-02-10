"""
The blueprint used for handling the jobs status
"""
from flask import Blueprint, jsonify, abort

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

    print('UPDATE JOB PROGRESS!')
    return jsonify({})