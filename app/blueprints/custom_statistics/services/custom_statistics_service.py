"""
Module that provides services for the custom statistics
"""
from app.models import delayed_job_models
import datetime

from app.config import RUN_CONFIG
from app.job_statistics import statistics_saver


class JobNotFoundError(Exception):
    """Base class for exceptions."""


def check_if_job_exists(job_id):
    """
    Checks if the job exists, if it exists, does nothing, if not, raises a JobNotFoundError
    :param job_id: id of the job to check
    """
    try:
        delayed_job_models.get_job_by_id(job_id, force_refresh=True)
    except delayed_job_models.JobNotFoundError:
        raise JobNotFoundError(f'Job with id {job_id} not found')


def save_custom_statistics_test_job(job_id, duration):
    """
    Saves the custom statistics for the test job
    :param job_id: id of the job, just as a test that the job exists
    :param duration: duration of the job
    """
    check_if_job_exists(job_id)

    doc = {
        'duration': int(duration),
        'date': datetime.datetime.utcnow().timestamp() * 1000
    }

    index_name = RUN_CONFIG.get('job_statistics').get('test_job_statistic_index')

    statistics_saver.save_record_to_elasticsearch(doc, index_name)
    return {'operation_result': 'Statistics successfully saved!'}


def save_custom_statistics_structure_search_job(job_id, search_type, time_taken):
    """
    Saves the custom statistics for the structure search job
    :param job_id: id of the job, just as a test that the job exists
    :param search_type: type of the search executed
    :param time_taken: time taken to do the search
    """
    check_if_job_exists(job_id)

    doc = {
        'search_type': search_type,
        'time_taken': time_taken,
        'host': 'delayed_jobs_k8s',
        'is_new': False,
        'request_date': datetime.datetime.utcnow().timestamp() * 1000,
        'run_env_type': RUN_CONFIG.get('run_env')
    }

    index_name = RUN_CONFIG.get('job_statistics').get('structure_search_job_statistics_index')

    statistics_saver.save_record_to_elasticsearch(doc, index_name)
    return {'operation_result': 'Statistics successfully saved!'}


def save_custom_statistics_mmv_job(job_id, num_sequences):
    """
    Saves the custom statistics for the mmv search job
    :param job_id: id of the job, just as a test that the job exists
    :param num_sequences: num sequences processed by the job
    """
    check_if_job_exists(job_id)

    doc = {
        'num_sequences': num_sequences,
        'request_date': datetime.datetime.utcnow().timestamp() * 1000,
    }

    index_name = RUN_CONFIG.get('job_statistics').get('mmv_job_statistics_index')

    statistics_saver.save_record_to_elasticsearch(doc, index_name)
    return {'operation_result': 'Statistics successfully saved!'}


def save_custom_statistics_download_job(job_id, time_taken, desired_format, file_size, es_index, es_query, total_items):
    """
    Saves the custom statistics for the download job
    :param job_id: id of the job, just as a test that the job exists
    :param time_taken: Time in seconds taken to do the download
    :param desired_format: Format requested for the download
    :param file_size: The resulting file size of the job in bytes
    :param es_index: Name of the index for which the download was generated
    :param es_query: Query used for the download
    :param total_items: The number of items saved in the file
    """
    check_if_job_exists(job_id)

    doc = {
        'desired_format': desired_format,
        'download_id': job_id,
        'es_index': es_index,
        'es_query': es_query,
        'file_size': file_size,
        'host': 'delayed_jobs_k8s',
        'is_new': False,
        'request_date': datetime.datetime.utcnow().timestamp() * 1000,
        'run_env_type': RUN_CONFIG.get('run_env'),
        'time_taken': time_taken,
        'total_items': total_items
    }

    index_name = RUN_CONFIG.get('job_statistics').get('download_job_statistics_index')
    statistics_saver.save_record_to_elasticsearch(doc, index_name)
    return {'operation_result': 'Statistics successfully saved!'}
