"""
This Module generates generic statistics for a job
"""
def get_seconds_from_created_to_queued(job):
    """
    :param job: DelayedJob object for which to do the caculation.
    :return: the amount of seconds that passed from the time the job was created to the time it
    was queued
    """
    created_at = job.created_at
    started_at = job.started_at
    return (started_at - created_at).total_seconds()
