"""
The blueprint used for handling the jobs status
"""
from flask import Blueprint, jsonify, request

from app.blueprints.job_status import job_status_service

JOB_STATUS_BLUEPRINT = Blueprint('job_status', __name__)

@JOB_STATUS_BLUEPRINT.route('/<job_id>')
def get_job_status(job_id):

    response = job_status_service.get_job_status(job_id)
    return jsonify(response)