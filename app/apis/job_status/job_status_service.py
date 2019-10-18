from app.apis.models import delayed_job_models


class JobNotFoundError(Exception):
    """Base class for exceptions."""
    pass


def get_job_status(id):

    try:
        job = delayed_job_models.get_job_by_id(id)
        return job.public_dict()
    except delayed_job_models.JobNotFoundError:
        raise JobNotFoundError()


def update_job_status(id, new_data):

    try:
        return delayed_job_models.update_job_status(id, new_data)
    except delayed_job_models.JobNotFoundError:
        raise JobNotFoundError()
