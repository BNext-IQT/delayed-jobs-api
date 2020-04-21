"""
This Module saves statistics for the jobs in elasticsearch
"""
def get_job_record_dict(job_type, run_env_type, lsf_host, started_at):
    """
    :param job_type: type of the job
    :param run_env_type: run environment
    :param lsf_host: lsf host
    :param started_at: started_at timestamp
    :return: a dict with a record of a job to be saved in elasticsearch
    """
    return {
        'job_type': job_type,
        'run_env_type': run_env_type,
        'lsf_host': lsf_host,
        'started_at': started_at
    }
