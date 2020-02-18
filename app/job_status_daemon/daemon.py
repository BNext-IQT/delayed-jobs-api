"""
Module that implements the daemon that checks the statuses of jobs in LSF
"""
from sqlalchemy import and_

from app.models import delayed_job_models
from app.config import RUN_CONFIG


def get_lsf_job_ids_to_check():
    """
    :return: a list of LSF job IDs for which it is necessary check the status in the LSF cluster. The jobs that are
    checked are the ones that:
    1. Were submitted to the same LSF cluster that I am running with (defined in configuration)
    2. Are not in Error or Finished state.
    """

    status_is_not_error_or_finished = delayed_job_models.DelayedJob.status.notin_(
        [delayed_job_models.JobStatuses.ERROR, delayed_job_models.JobStatuses.FINISHED]
    )

    lsf_config = RUN_CONFIG.get('lsf_submission')
    lsf_host = lsf_config['lsf_host']
    lsf_host_is_my_host = delayed_job_models.DelayedJob.lsf_host == lsf_host

    job_to_check_status = delayed_job_models.DelayedJob.query.filter(
        and_(lsf_host_is_my_host, status_is_not_error_or_finished)
    )

    return [job.lsf_job_id for job in job_to_check_status]
