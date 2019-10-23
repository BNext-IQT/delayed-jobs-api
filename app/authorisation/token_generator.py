import datetime
from app.config import RUN_CONFIG
import jwt

JOB_TOKEN_HOURS_TO_LIVE = 24


def generate_job_token(job_id):

    token_data = {
        'job_id': job_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=JOB_TOKEN_HOURS_TO_LIVE)
    }

    key = RUN_CONFIG.get('server_secret_key')
    token = jwt.encode(token_data, key).decode('UTF-8')

    return token
