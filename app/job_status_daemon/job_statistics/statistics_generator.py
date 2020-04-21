"""
This Module generates generic statistics for a job
"""
import os


def get_seconds_from_created_to_queued(job):
    """
    :param job: DelayedJob object for which to do the calculation.
    :return: the amount of seconds that passed from the time the job was created to the time it
    was queued
    """
    created_at = job.created_at
    started_at = job.started_at
    return (started_at - created_at).total_seconds()

def get_seconds_from_running_to_finished(job):
    """
    :param job: DelayedJob object for which to do the calculation.
    :return: the amount of seconds that passed from the time the job was running to the time it
    was finished
    """
    started_at = job.started_at
    finished_at = job.finished_at
    return (finished_at - started_at).total_seconds()

def get_num_input_files_of_job(job):
    """
    :param job: DelayedJob object for which to do the calculation.
    :return: the number of input file that a job has
    """
    return len(job.input_files)

def get_total_bytes_of_input_files_of_job(job):
    """
    :param job: DelayedJob object for which to do the calculation.
    :return: the total bytes of input the file that a job has
    """
    total_input_bytes = 0

    for job_input_file in job.input_files:

        path = job_input_file.internal_path
        current_file_size = os.path.getsize(path)
        total_input_bytes += current_file_size

    return total_input_bytes