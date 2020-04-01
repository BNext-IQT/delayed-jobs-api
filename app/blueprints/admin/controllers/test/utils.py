"""
Module with utils functions for the admin tasks tests
"""
import os
import random
import string

from app.models import delayed_job_models


def simulate_inputs_to_job(job, job_run_dir):
    """
    Creates some input files and adds it to the job object
    :param job: job to add the input files to
    :param job_run_dir: directory where the job runs
    """
    inputs_path = os.path.join(job_run_dir, 'inputs')
    for i in range(1, 5):
        input_path = os.path.join(inputs_path, f'input{i}.txt')
        with open(inputs_path, 'w') as input_file:
            input_file.write(f'This is input {i}')

        job_input_file = delayed_job_models.InputFile(internal_path=input_path)
        delayed_job_models.add_input_file_to_job(job, job_input_file)


def simulate_outputs_of_job(job, output_dir):

    """
    Creates some output files and adds it to the job object
    :param job: job to add the output files to
    :param output_dir: directory where the job writes the outputs
    """
    outputs_path = os.path.join(output_dir, 'outputs')
    for i in range(1, 5):
        output_path = os.path.join(outputs_path, f'output{i}.txt')
        with open(outputs_path, 'w') as output_file:
            output_file.write(f'This is output {i}')

        job_output_file = delayed_job_models.OutputFile(internal_path=output_path)
        delayed_job_models.add_output_file_to_job(job, job_output_file)


def simulate_finished_job(run_dir_path, expires_at=None):
    """
    Creates a database a job that is finished. It will expire at the date passed as parameter.
    :param run_dir_path: path of the run dir of the job
    :param expires_at: Expiration date that you want for the job. None if it is not necessary for your test
    """

    # create a job
    job_type = 'SIMILARITY'
    params = {
        'search_type': 'SIMILARITY',
        'structure': ''.join(random.choice(string.ascii_lowercase) for i in range(10)),
        'threshold': '70'
    }
    docker_image_url = 'some_url'

    job = delayed_job_models.get_or_create(job_type, params, docker_image_url)
    # simulate it finished

    job_run_dir = os.path.join(run_dir_path, job.id)
    job.run_dir_path = job_run_dir
    os.makedirs(job_run_dir, exist_ok=True)

    output_dir = os.path.join(run_dir_path, job.id).join('outputs')
    job.output_dir_path = output_dir
    os.makedirs(output_dir, exist_ok=True)

    # Add some inputs
    simulate_inputs_to_job(job, job_run_dir)

    # Add some outputs
    simulate_outputs_of_job(job, output_dir)

    job.status = delayed_job_models.JobStatuses.FINISHED
    job.expires_at = expires_at
    delayed_job_models.save_job(job)

    return job