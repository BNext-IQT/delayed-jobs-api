"""
Blueprint for the administrative tasks of the system
"""
from flask import Blueprint, jsonify, request, make_response

ADMIN_TASKS_BLUEPRINT = Blueprint('admin_tasks', __name__)

@ADMIN_TASKS_BLUEPRINT.route('/delete_all_jobs_by_type', methods = ['POST'])
def delete_all_jobs_by_type():
    return jsonify({'operation_result': 'Done'})