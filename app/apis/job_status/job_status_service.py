from app.apis.models import delayed_job_models
import os
from flask import url_for


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


def save_uploaded_file(id, file):

    try:
        job = delayed_job_models.get_job_by_id(id)
        print(f'Receiving file for {id}')
        output_dir_path = job.output_dir_path
        output_file_path = os.path.join(output_dir_path, file.filename)
        print(f'Saving file to {output_file_path}')
        file.save(output_file_path)
        job.output_file_path = output_file_path
        output_file_url = url_for('static', filename=f'jobs_output/{job.id}/{file.filename}')
        job.output_file_url = output_file_url
        delayed_job_models.save_job(job)
        return {
            'result': 'File received successfully'
        }
    except delayed_job_models.JobNotFoundError:
        raise JobNotFoundError()
