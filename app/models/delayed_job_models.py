"""
    Module with the classes related to the job model
"""
import json
import hashlib
import base64
from enum import Enum
from app.models.db import db
import datetime


class JobTypes(Enum):
    """
        Types of delayed jobs
    """
    SIMILARITY = 'SIMILARITY'
    SUBSTRUCTURE = 'SUBSTRUCTURE'
    CONNECTIVITY = 'CONNECTIVITY'
    BLAST = 'BLAST'
    DOWNLOAD = 'DOWNLOAD'

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name


class JobStatuses(Enum):
    """
        Possible statuses of delayed jobs
    """
    CREATED = 'CREATED'
    QUEUED = 'QUEUED'
    RUNNING = 'RUNNING'
    ERROR = 'ERROR'
    FINISHED = 'FINISHED'

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name


class DelayedJob(db.Model):
    id = db.Column(db.String(length=60), primary_key=True)
    type = db.Column(db.Enum(JobTypes))
    status = db.Column(db.Enum(JobStatuses), default=JobStatuses.CREATED)
    status_comment = db.Column(db.String) # a comment about the status, for example 'Compressing file'
    progress = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    started_at = db.Column(db.DateTime)
    finished_at = db.Column(db.DateTime)
    output_file_path = db.Column(db.Text)
    log = db.Column(db.Text)
    raw_params = db.Column(db.Text)
    expires = db.Column(db.DateTime)
    api_initial_url = db.Column(db.Text)
    timezone = db.Column(db.String(length=60), default=str(datetime.timezone.utc))

    def __repr__(self):
        return f'<DelayedJob ${self.id} ${self.type} ${self.status}>'

    def public_dict(self):
        """
        Returns a dictionary representation of the object with all the fields that are safe to be public
        :return:
        """
        return {key:str(getattr(self, key)) for key in ['id', 'type', 'status', 'status_comment', 'progress',
                                                        'created_at', 'started_at', 'finished_at', 'output_file_path',
                                                        'raw_params', 'expires', 'api_initial_url', 'timezone']}

def generate_job_id(job_type, job_params):
    """
    Generates a job id from a sha 256 hash of the string version of the job params in base 64
    :param job_type: type of job run
    :param job_params: parameters for the job
    :return: The id that the job must have
'    """

    stable_raw_search_params = json.dumps(job_params, sort_keys=True)
    search_params_digest = hashlib.sha256(stable_raw_search_params.encode('utf-8')).digest()
    base64_search_params_digest = base64.b64encode(search_params_digest).decode('utf-8').replace('/', '_').replace(
        '+', '-')

    return '{}-{}'.format(repr(job_type), base64_search_params_digest)


def get_or_create(job_type, job_params):

    id = generate_job_id(job_type, job_params)

    existing_job = DelayedJob.query.filter_by(id=id).first()
    if existing_job is not None:
        return existing_job

    job = DelayedJob(id=id, type=job_type, raw_params=json.dumps(job_params))

    db.session.add(job)
    db.session.commit()
    return job
