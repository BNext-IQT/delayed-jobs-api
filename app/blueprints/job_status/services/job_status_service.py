"""
Module that provides a service to get or modify the status or jobs
"""
from app.models import delayed_job_models

class JobNotFoundError(Exception):
    """Base class for exceptions."""

class InputFileNotFoundError(Exception):
    """Base class for exceptions."""


def get_job_status(job_id, server_base_url='http://0.0.0.0:5000'):
    """
    Returns a dict representation of the job with the id given as parameter
    :param job_id: the id of the job for which the status is required
    :param server_base_url: url to use as base for building the output files urls
    :return: a dict with the public properties of a job.
    """

    try:

        job = delayed_job_models.get_job_by_id(job_id, force_refresh=True)
        return job.public_dict(server_base_url)
    except delayed_job_models.JobNotFoundError:
        raise JobNotFoundError()

def get_input_file_path(job_id, input_key):
    """
    :param job_id: the id of the job for which the status is required
    :param input_key: input_key as saved in the database
    :return: the internal path of an input file to be used to be sent as a response
    """

    try:
        input_file = delayed_job_models.get_job_input_file(job_id, input_key)
        return input_file.internal_path
    except delayed_job_models.InputFileNotFoundError:
        raise InputFileNotFoundError()


def update_job_progress(job_id, progress, status_log, status_description):
    """
    Updates the status of the job wit the id given as parameter.
    :param job_id: job_id of the job to modify
    :param progress: the progress percentage of the job
    :param status_log: a message to append to the public job status log
    :return: a dict with the public properties of a job.
    """

    try:
        delayed_job_models.update_job_progress(job_id, progress, status_log, status_description)
        job = delayed_job_models.get_job_by_id(job_id)
        return job.public_dict()
    except delayed_job_models.JobNotFoundError:
        raise JobNotFoundError()
