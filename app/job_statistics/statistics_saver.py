"""
This Module saves statistics for the jobs in elasticsearch
"""
from app.config import RUN_CONFIG
from app import app_logging
from app.config import ImproperlyConfiguredError
from app.es_connection import ES


def get_job_record_dict(job_type, run_env_type, lsf_host, started_at, finished_at,
                        seconds_taken_from_created_to_running, seconds_taken_from_running_to_finished_or_error,
                        final_state, num_output_files, total_output_bytes, num_input_files, total_input_bytes):
    """
    :param job_type: type of the job
    :param run_env_type: run environment
    :param lsf_host: lsf host
    :param started_at: started_at timestamp
    :param finished_at: finished_at timestamp
    :param seconds_taken_from_created_to_running: seconds_taken_from_created_to_running
    :param seconds_taken_from_running_to_finished_or_error: seconds_taken_from_running_to_finished_or_error
    :param final_state: final_state of the job
    :param num_output_files: number of output files of the job
    :param total_output_bytes: total output of bytes of the job
    :param num_input_files: number of input files of the job
    :param total_input_bytes: total input of bytes of the job
    :return: a dict with a record of a job to be saved in elasticsearch
    """
    return {
        'job_type': job_type,
        'run_env_type': run_env_type,
        'lsf_host': lsf_host,
        'started_at': started_at,
        'finished_at': finished_at,
        'seconds_taken_from_created_to_running': seconds_taken_from_created_to_running,
        'seconds_taken_from_running_to_finished_or_error': seconds_taken_from_running_to_finished_or_error,
        'final_state': final_state,
        'num_output_files': num_output_files,
        'total_output_bytes': total_output_bytes,
        'num_input_files': num_input_files,
        'total_input_bytes': total_input_bytes
    }

def save_job_record(job_type, run_env_type, lsf_host, started_at, finished_at,
                    seconds_taken_from_created_to_running, seconds_taken_from_running_to_finished_or_error,
                    final_state, num_output_files, total_output_bytes, num_input_files, total_input_bytes):
    """
    Saves the job record in elasticsearch with the parameters given
    :param job_type: type of the job
    :param run_env_type: run environment
    :param lsf_host: lsf host
    :param started_at: started_at timestamp
    :param finished_at: finished_at timestamp
    :param seconds_taken_from_created_to_running: seconds_taken_from_created_to_running
    :param seconds_taken_from_running_to_finished_or_error: seconds_taken_from_running_to_finished_or_error
    :param final_state: final_state of the job
    :param num_output_files: number of output files of the job
    :param total_output_bytes: total output of bytes of the job
    :param num_input_files: number of input files of the job
    :param total_input_bytes: total input of bytes of the job
    :return: a dict with a record of a job to be saved in elasticsearch
    """

    job_record_dict = get_job_record_dict(
        job_type=str(job_type),
        run_env_type=str(run_env_type),
        lsf_host=lsf_host,
        started_at=started_at,
        finished_at=finished_at,
        seconds_taken_from_created_to_running=seconds_taken_from_created_to_running,
        seconds_taken_from_running_to_finished_or_error=seconds_taken_from_running_to_finished_or_error,
        final_state=str(final_state),
        num_output_files=num_output_files,
        total_output_bytes=total_output_bytes,
        num_input_files=num_input_files,
        total_input_bytes=total_input_bytes
    )

    index_name = RUN_CONFIG.get('job_statistics').get('general_statistics_index')

    if index_name is None:
        raise ImproperlyConfiguredError('You must provide an index name to save job statistics in'
                                        ' job_statistics.general_statistics_index')

    save_record_to_elasticsearch(job_record_dict, index_name)


def get_job_cache_record_dict(job_type, run_env_type, was_cached, request_date):
    """
    :param job_type: the type of the job
    :param run_env_type: run environment
    :param was_cached: if the record was cached or not
    :param request_date: timestamp of the date the request was made
    :return: a dict to be used to save the job cache statistics in the elasticsearch index
    """
    return {
        'job_type': str(job_type),
        'run_env_type': str(run_env_type),
        'was_cached': was_cached,
        'request_date': request_date
    }

def save_job_cache_record(job_type, run_env_type, was_cached, request_date):
    """
     a dict to be used to save the job cache statistics in the elasticsearch index
    :param job_type: the type of the job
    :param run_env_type: run environment
    :param was_cached: if the record was cached or not
    :param request_date: timestamp of the date the request was made
   """

    job_cache_record_dict = get_job_cache_record_dict(job_type, run_env_type, was_cached, request_date)
    index_name = RUN_CONFIG.get('job_statistics').get('cache_statistics_index')

    if index_name is None:
        raise ImproperlyConfiguredError('You must provide an index name to save job statistics in'
                                        ' job_statistics.cache_statistics_index')

    save_record_to_elasticsearch(job_cache_record_dict, index_name)

# ----------------------------------------------------------------------------------------------------------------------
# Saving records to elasticsearch
# ----------------------------------------------------------------------------------------------------------------------
def save_record_to_elasticsearch(doc, index_name):

    dry_run = RUN_CONFIG.get('job_statistics', {}).get('dry_run', False)

    if dry_run:
        app_logging.debug(f'Not actually sending the record to the statistics (dry run): {doc}')
    else:
        app_logging.debug(f'Sending the following record to the statistics: {doc}')
        result = ES.index(index=index_name, body=doc, doc_type='_doc')
        app_logging.debug(f'Result {result}')