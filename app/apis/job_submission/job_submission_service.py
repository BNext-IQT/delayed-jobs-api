"""
This module submits jobs to the EBI queue
"""
from app.apis.models import delayed_job_models
import jwt
import datetime
from app.config import RUN_CONFIG



JOB_TOKEN_HOURS_TO_LIVE = 24


def submit_job(job_type, job_params):
    """Submit job to the queue"""
    job = delayed_job_models.get_or_create(job_type, job_params)
    print('LOOK AT ME, I AM SUBMITTING A JOB!')
    print('')
    return {
        "status": "job submitted"
    }


def generate_job_token(job_id):

    token_data = {
        'job_id': job_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=JOB_TOKEN_HOURS_TO_LIVE)
    }

    key = RUN_CONFIG.get('server_secret_key')
    token = jwt.encode(token_data, key).decode('UTF-8')

    return token


