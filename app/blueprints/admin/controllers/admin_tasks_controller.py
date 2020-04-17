"""
Blueprint for the administrative tasks of the system
"""
from flask import Blueprint, jsonify, request

from app.blueprints.admin.services import admin_tasks_service
from app.authorisation.decorators import admin_token_required
from app.blueprints.admin.controllers import marshmallow_schemas
from app.request_validation.decorators import validate_form_with, validate_url_params_with

ADMIN_TASKS_BLUEPRINT = Blueprint('admin_tasks', __name__)

@ADMIN_TASKS_BLUEPRINT.route('/delete_all_jobs_by_type', methods = ['POST'])
@admin_token_required
@validate_form_with(marshmallow_schemas.DeleteAllJobsByTypeOperation)
def delete_all_jobs_by_type():

    form_data = request.form
    job_type = form_data.get('job_type')
    operation_result = admin_tasks_service.delete_all_jobs_by_type(job_type)
    return jsonify({'operation_result': operation_result})

@ADMIN_TASKS_BLUEPRINT.route('/delete_output_files_for_job/<job_id>', methods = ['GET'])
@admin_token_required
@validate_url_params_with(marshmallow_schemas.DeleteAllOutputsOfJobOperation)
def delete_output_files_for_job(job_id):

    operation_result = admin_tasks_service.delete_all_outputs_of_job(job_id)
    return jsonify({'operation_result': operation_result})

@ADMIN_TASKS_BLUEPRINT.route('/delete_expired_jobs', methods = ['GET'])
@admin_token_required
def delete_output_files_for_job():

    operation_result = admin_tasks_service.delete_expired_jobs()
    return jsonify({'operation_result': operation_result})