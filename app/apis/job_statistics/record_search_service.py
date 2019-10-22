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

        calculated_statistics = {
            **statistics,
            'is_new': False,
            'time_taken': int((job.finished_at - job.started_at).total_seconds()),
            'type': job.type,
            'request_date': job.started_at.timestamp()
        }

        return calculated_statistics
    except delayed_job_models.JobNotFoundError:
        raise JobNotFoundError()
