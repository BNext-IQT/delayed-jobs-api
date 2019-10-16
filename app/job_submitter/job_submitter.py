"""
This module submits jobs to the EBI queue
"""
import app.models.delayed_job_models as Job


def submit_job(job_type, job_params):
    """Submit job to the queue"""
    job = Job.get_or_create(job_type, job_params)
    print('LOOK AT ME, I AM SUBMITTING A JOB!')
    print('')
    return {
        "status": "job submitted"
    }
