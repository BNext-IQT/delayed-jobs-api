"""
This Module receives the requests for the custom statistics
"""
from flask import Blueprint, jsonify, request, abort

from app.blueprints.custom_statistics.controllers import marshmallow_schemas
from app.request_validation.decorators import validate_form_with, validate_url_params_with
from app.authorisation.decorators import token_required_for_job_id
from app.blueprints.custom_statistics.services import custom_statistics_service

CUSTOM_STATISTICS_BLUEPRINT = Blueprint('custom_statistics', __name__)


@CUSTOM_STATISTICS_BLUEPRINT.route('/submit_statistics/test_job/<job_id>', methods=['POST'])
@token_required_for_job_id
@validate_url_params_with(marshmallow_schemas.JobID)
@validate_form_with(marshmallow_schemas.TestJobStatistics)
def submit_custom_statistics_test_job(job_id):
    try:
        duration = request.form.get('duration')
        return jsonify(custom_statistics_service.save_custom_statistics_test_job(job_id, duration))
    except custom_statistics_service.JobNotFoundError:
        abort(404, f'Job with id {job_id} does not exist!')


@CUSTOM_STATISTICS_BLUEPRINT.route('/submit_statistics/structure_search_job/<job_id>', methods=['POST'])
@token_required_for_job_id
@validate_url_params_with(marshmallow_schemas.JobID)
@validate_form_with(marshmallow_schemas.StructureSearchJobStatistics)
def submit_custom_statistics_structure_search_job(job_id):
    try:
        search_type = request.form.get('search_type')
        time_taken = request.form.get('time_taken')
        return jsonify(custom_statistics_service.save_custom_statistics_structure_search_job(
            job_id, search_type, time_taken))
    except custom_statistics_service.JobNotFoundError:
        abort(404, f'Job with id {job_id} does not exist!')


@CUSTOM_STATISTICS_BLUEPRINT.route('/submit_statistics/biological_sequence_search_job/<job_id>', methods=['POST'])
@token_required_for_job_id
@validate_url_params_with(marshmallow_schemas.JobID)
@validate_form_with(marshmallow_schemas.BiologicalSequenceSearchJobStatistics)
def submit_custom_statistics_biological_sequence_search_job(job_id):
    try:
        search_type = 'BLAST'
        time_taken = request.form.get('time_taken')
        return jsonify(custom_statistics_service.save_custom_statistics_structure_search_job(
            job_id, search_type, time_taken))
    except custom_statistics_service.JobNotFoundError:
        abort(404, f'Job with id {job_id} does not exist!')


@CUSTOM_STATISTICS_BLUEPRINT.route('/submit_statistics/mmv_job/<job_id>', methods=['POST'])
@token_required_for_job_id
@validate_url_params_with(marshmallow_schemas.JobID)
@validate_form_with(marshmallow_schemas.MMVSearchJobStatistics)
def submit_custom_statistics_mmv_job(job_id):
    try:
        num_sequences = request.form.get('num_sequences')
        return jsonify(custom_statistics_service.save_custom_statistics_mmv_job(job_id, num_sequences))
    except custom_statistics_service.JobNotFoundError:
        abort(404, f'Job with id {job_id} does not exist!')


@CUSTOM_STATISTICS_BLUEPRINT.route('/submit_statistics/download_job/<job_id>', methods=['POST'])
@token_required_for_job_id
@validate_url_params_with(marshmallow_schemas.JobID)
@validate_form_with(marshmallow_schemas.DownloadJobStatistics)
def submit_custom_statistics_download_job(job_id):
    try:
        time_taken = request.form.get('time_taken')
        desired_format = request.form.get('desired_format')
        file_size = request.form.get('file_size')
        es_index = request.form.get('es_index')
        es_query = request.form.get('es_query')
        total_items = request.form.get('total_items')
        return jsonify(
            custom_statistics_service.save_custom_statistics_download_job(job_id, time_taken, desired_format, file_size,
                                                                          es_index, es_query, total_items))
    except custom_statistics_service.JobNotFoundError:
        abort(404, f'Job with id {job_id} does not exist!')
