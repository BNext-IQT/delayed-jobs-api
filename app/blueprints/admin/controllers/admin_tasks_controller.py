"""
Blueprint for the administrative tasks of the system
"""
from flask import Blueprint, jsonify, request, make_response

from app.blueprints.admin.services import admin_tasks_service
from app.authorisation.decorators import admin_token_required

ADMIN_TASKS_BLUEPRINT = Blueprint('admin_tasks', __name__)

@ADMIN_TASKS_BLUEPRINT.route('/delete_all_jobs_by_type', methods = ['POST'])
@admin_token_required
def delete_all_jobs_by_type():

    form_data = request.form
    job_type = form_data.get('job_type')
    operation_result = admin_tasks_service.delete_all_jobs_by_type(job_type)
    return jsonify({'operation_result': operation_result})