from app.apis.models import delayed_job_models
from app.config import RUN_CONFIG
from elasticsearch import Elasticsearch
es = Elasticsearch()


class JobNotFoundError(Exception):
    """Base class for exceptions."""
    pass


class JobNotFinishedError(Exception):
    """Base class for exceptions."""
    pass


def save_statistics_for_job(id, statistics):

    try:
        job = delayed_job_models.get_job_by_id(id)
        if job.status != delayed_job_models.JobStatuses.FINISHED:
            raise JobNotFinishedError()

        calculated_statistics = {
            **statistics,
            'is_new': False,
            'time_taken': int((job.finished_at - job.started_at).total_seconds()),
            'search_type': job.type,
            'request_date': job.started_at.timestamp()
        }
        save_search_record_to_elasticsearch(calculated_statistics)

        return calculated_statistics
    except delayed_job_models.JobNotFoundError:
        raise JobNotFoundError()

def save_search_record_to_elasticsearch(calculated_statistics):

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
        res = es.search(index="test-index", body={"query": {"match_all": {}}})

