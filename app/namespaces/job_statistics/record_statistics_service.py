"""
Module that describes and handles the requests concerned with recording statistics
"""
from app.namespaces.models import delayed_job_models
from app.config import RUN_CONFIG
from app.es_connection import ES


class JobNotFoundError(Exception):
    """Base class for exceptions."""


class JobNotFinishedError(Exception):
    """Base class for exceptions."""


def save_statistics_for_job(job_id, statistics):
    """
    Saves statistics (Remember to rethink this)
    :param job_id:
    :param statistics:
    :return:
    """

    try:
        job = delayed_job_models.get_job_by_id(job_id)
        if job.status != delayed_job_models.JobStatuses.FINISHED:
            raise JobNotFinishedError()

        calculated_statistics = calculate_extra_and_save_statistics_to_elasticsearch(job, statistics)
        return calculated_statistics

    except delayed_job_models.JobNotFoundError:
        raise JobNotFoundError()


def calculate_extra_and_save_statistics_to_elasticsearch(job, statistics):
    """

    :param job:
    :param statistics:
    :return:
    """

    calculated_statistics = {
        **statistics,
        'is_new': False,
        'time_taken': int((job.finished_at - job.started_at).total_seconds()),
        'search_type': job.type,
        'request_date': job.started_at.timestamp()
    }
    save_search_record_to_elasticsearch(calculated_statistics)

    return calculated_statistics


def save_search_record_to_elasticsearch(calculated_statistics):
    """

    :param calculated_statistics:
    :return:
    """

    es_index = 'chembl_glados_es_search_record'
    es_doc = {
        **calculated_statistics,
        'run_env': RUN_CONFIG.get('run_env')
    }

    if RUN_CONFIG.get('elasticsearch').get('dry_run', False):
        print('---------------------------------------------------')
        print('Elasticsearch Dry Run')
        print('I would have saved this doc')
        print('es_index: ', es_index)
        print(es_doc)
        print('---------------------------------------------------')
    else:
        print('SAVING TO ES')
        ES.search(index=es_index, body={"query": {"match_all": {}}})
