"""
Module with utils for these tests
"""
import os

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