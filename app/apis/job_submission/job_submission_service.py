"""
This module submits jobs to the EBI queue
"""
from app.apis.models import delayed_job_models
from app.config import RUN_CONFIG
from pathlib import Path
import os
import stat
from app.authorisation import token_generator
import shutil


JOBS_RUN_DIR = RUN_CONFIG.get('jobs_run_dir')
if JOBS_RUN_DIR is None:
    JOBS_RUN_DIR = str(Path().absolute()) + '/jobs_run'
    os.makedirs(JOBS_RUN_DIR, exist_ok=True)

print('------------------------------------------------------------------------------')
print('JOBS_RUN_DIR: ', JOBS_RUN_DIR)
print('------------------------------------------------------------------------------')

JOBS_SCRIPTS_DIR = str(Path().absolute()) + '/jobs_scripts'

RUN_PARAMS_FILENAME = 'run_params.yml'

SCRIPT_FILENAMES = {
    f'{delayed_job_models.JobTypes.SIMILARITY}': 'structure_search.py'
}

SCRIPT_FILES = {
    f'{delayed_job_models.JobTypes.SIMILARITY}':
        os.path.join(JOBS_SCRIPTS_DIR, SCRIPT_FILENAMES.get(str(delayed_job_models.JobTypes.SIMILARITY))),
}


def submit_job(job_type, job_params):
    """Submit job to the queue"""
    job = delayed_job_models.get_or_create(job_type, job_params)
    job_run_dir = os.path.join(JOBS_RUN_DIR, job.id)
    os.makedirs(job_run_dir, exist_ok=True)

    template_run_params_path = os.path.join(Path().absolute(), 'templates', 'run_params_template.yml')
    template_file = open(template_run_params_path, 'r')
    run_params_template = template_file.read()
    template_file.close()
    job_token = token_generator.generate_job_token(job.id)

    run_params = run_params_template.format(
        JOB_ID=job.id,
        JOB_TOKEN=job_token,
        STATUS_UPDATE_URL=f'http://127.0.0.1:5000/status/{job.id}',
        STATUS_UPDATE_METHOD='PATCH',
        STATISTICS_URL=f'http://127.0.0.1:5000/record/search/{job.id}',
        STATISTICS_METHOD='POST',
        JOB_PARAMS=f'{job.raw_params}'
    )

    run_params_path = os.path.join(job_run_dir, RUN_PARAMS_FILENAME)

    # delete file if existed before, just in case
    if os.path.exists(run_params_path):
        os.remove(run_params_path)

    with open(run_params_path, "w") as out_file:
        out_file.write(run_params)

    job_script = SCRIPT_FILES.get(str(job.type))
    run_script_path = os.path.join(job_run_dir, SCRIPT_FILENAMES.get(str(job.type)))
    shutil.copyfile(job_script, run_script_path)

    # make sure file is executable
    st = os.stat(run_script_path)
    os.chmod(run_script_path, st.st_mode | stat.S_IEXEC)

    return job.public_dict()

