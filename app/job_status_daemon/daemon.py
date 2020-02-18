"""
Module that implements the daemon that checks the statuses of jobs in LSF
"""
import os
from pathlib import Path
import socket
from datetime import datetime

from sqlalchemy import and_

from app.models import delayed_job_models
from app.config import RUN_CONFIG

AGENT_RUN_DIR = RUN_CONFIG.get('status_agent_run_dir', str(Path().absolute()) + '/status_agents_run')
if not os.path.isabs(AGENT_RUN_DIR):
    AGENT_RUN_DIR = Path(AGENT_RUN_DIR).resolve()
os.makedirs(AGENT_RUN_DIR, exist_ok=True)

print('------------------------------------------------------------------------------')
print(f'AGENT_RUN_DIR: {AGENT_RUN_DIR}')
print('------------------------------------------------------------------------------')


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

def get_check_job_status_script_path():
    """
    :return: the path to use for creating the job status script
    """

    filename = f'{datetime.now().strftime("%Y-%m-%d-%H-%M-%S")}_check_lsf_job_status.sh'
    job_status_check_script_path = Path(AGENT_RUN_DIR).joinpath(socket.gethostname(), filename)

    return job_status_check_script_path

def prepare_job_status_check_script(lsf_job_ids):
    """
    Prepares the script that will check for the job status to LSF
    :lsf_job_ids: the list of job ids for which check the status
    :return: the final path of the script that was created
    """

    job_status_script_template_path = os.path.join(Path().absolute(), 'templates', 'get_jobs_status.sh')
    with open(job_status_script_template_path, 'r') as template_file:
        job_status_template = template_file.read()

        lsf_config = RUN_CONFIG.get('lsf_submission')
        lsf_user = lsf_config['lsf_user']
        lsf_host = lsf_config['lsf_host']

        job_submission_script = job_status_template.format(
            LSF_JOB_IDS=' '.join([str(lsf_job_id) for lsf_job_id in lsf_job_ids]),
            LSF_USER=lsf_user,
            LSF_HOST=lsf_host
        )

        status_script_path = get_check_job_status_script_path()
        status_script_path.parent.mkdir(parents=True, exist_ok=True)
        with open(status_script_path, 'w') as status_script_file:
            status_script_file.write(job_submission_script)

    return status_script_path
