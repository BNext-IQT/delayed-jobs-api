"""
Module with utils for these tests
"""
import os

from app.models import delayed_job_models

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