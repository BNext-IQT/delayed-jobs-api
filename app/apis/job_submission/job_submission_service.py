"""
This module submits jobs to the EBI queue
"""
from app.apis.models import delayed_job_models
from app.config import RUN_CONFIG
from pathlib import Path
import os
from app.authorisation import token_generator


JOBS_RUN_DIR = RUN_CONFIG.get('jobs_run_dir')
if JOBS_RUN_DIR is None:
    JOBS_RUN_DIR = str(Path().absolute()) + '/jobs_run'
    os.makedirs(JOBS_RUN_DIR, exist_ok=True)

print('------------------------------------------------------------------------------')
print('JOBS_RUN_DIR: ', JOBS_RUN_DIR)
print('------------------------------------------------------------------------------')

RUN_PARAMS_FILENAME = 'run_params.yml'


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
        JOB_TOKEN=job_token
    )

    run_params_path = os.path.join(job_run_dir, RUN_PARAMS_FILENAME)

    with open(run_params_path, "w") as out_file:
        print(run_params, file=out_file)

    return job.public_dict()


# def generate_job_token(job_id):
#
#     token_data = {
#         'job_id': job_id,
#         'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=token_generator.JOB_TOKEN_HOURS_TO_LIVE)
#     }
#
#     key = RUN_CONFIG.get('server_secret_key')
#     token = jwt.encode(token_data, key).decode('UTF-8')
#
#     return token


