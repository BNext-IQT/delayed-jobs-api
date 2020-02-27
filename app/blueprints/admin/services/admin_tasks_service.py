"""
Module that provide services for administrative tasks of the system
"""
from app.models import delayed_job_models

def delete_all_jobs_by_type(job_type):
    """
    Triggers the deletion of the jobs of the given type
    :param job_type: type of the job to delete
    :return: a message (string) with the result of the operation
    """
    num_deleted = delayed_job_models.delete_all_jobs_by_type(job_type)
    return f'All {num_deleted} jobs of type {job_type} were deleted!'
