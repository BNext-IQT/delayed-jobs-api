from app.apis.models import delayed_job_models


class JobNotFoundError(Exception):
    """Base class for exceptions."""
    pass


class JobNotFinishedError(Exception):
    """Base class for exceptions."""
    pass

def save_statistics_for_job(id, statistics):

    try:
        job = delayed_job_models.get_job_by_id(id)
        if job.status != delayed_job_models.JobStatuses.FINISHED:
            raise JobNotFinishedError()
        return statistics
    except delayed_job_models.JobNotFoundError:
        raise JobNotFoundError()
