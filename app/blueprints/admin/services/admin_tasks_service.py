"""
Module that provide services for administrative tasks of the system
"""
import os
from pathlib import Path
import shutil

from flask import abort

from app.models import delayed_job_models


class JobNotFoundError(Exception):
    """Base class for exceptions."""


def delete_all_jobs_by_type(job_type):
    """
    Triggers the deletion of the jobs of the given type
    :param job_type: type of the job to delete
    :return: a message (string) with the result of the operation
    """
    num_deleted = delayed_job_models.delete_all_jobs_by_type(job_type)
    return f'All {num_deleted} jobs of type {job_type} were deleted!'

def delete_all_outputs_of_job(job_id):
    """
    Deletes all the outputs of the job of the job given as parameter. The job must be in FINISHED state
    :param job_id: id of the job for which the outputs will be deleted.
    :return:
    """
    try:
        job = delayed_job_models.get_job_by_id(job_id)
        output_dir_path = job.output_dir_path

        for item in os.listdir(output_dir_path):
            item_path = str(Path(output_dir_path).joinpath(item))
            try:
                shutil.rmtree(item_path)
            except NotADirectoryError:
                os.remove(item_path)

        return f'All outputs of the job {job_id} were deleted!'
    except delayed_job_models.JobNotFoundError:
        raise abort(404)
