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

def delete_all_outputs_of_jobs(job_id):
    """
    Deletes all the outputs of the job of the job given as parameter. The job must be in FINISHED state
    :param job_id: id of the job for which the outputs will be deleted.
    :return:
    """
    return f'All outputs of the job {job_id} were deleted!'
