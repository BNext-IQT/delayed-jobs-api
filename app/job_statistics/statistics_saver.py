"""
This Module saves statistics for the jobs in elasticsearch
"""
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
