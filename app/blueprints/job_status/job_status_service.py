"""
Module that provides a service to get or modify the status or jobs
"""
import os

from flask import url_for

from app.models import delayed_job_models


class JobNotFoundError(Exception):
    """Base class for exceptions."""


def get_job_status(job_id):
    """
    Returns a dict representation of the job with the id given as parameter
    :param job_id: the id of the job for which the status is required
    :return: a dict with the public properties of a job.
    """

    try:
        job = delayed_job_models.get_job_by_id(job_id)
        return job.public_dict()
    except delayed_job_models.JobNotFoundError:
        raise JobNotFoundError()


def update_job_status(job_id, new_data):
    """
    Updates the status of the job wit the id given as parameter.
    :param job_id: job_id of the job to modify
    :param new_data: a dict with the properties and their new values
    :return: a dict with the public properties of a job.
    """

    try:
        return delayed_job_models.update_job_status(job_id, new_data)
    except delayed_job_models.JobNotFoundError:
        raise JobNotFoundError()
