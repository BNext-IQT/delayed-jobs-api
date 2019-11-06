"""
    Module with the classes related to the job model
"""
import base64
import datetime
import hashlib
import json
from enum import Enum
from app.db import db
import shutil


DAYS_TO_LIVE = 7  # Days for which the results are kept


class JobTypes(Enum):
    """
        Types of delayed jobs
    """
    TEST = 'TEST'
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


class JobNotFoundError(Exception):
    """Base class for exceptions."""
    pass


class JobExecution(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hostname = db.Column(db.String(length=500), nullable=False)
    command = db.Column(db.String(length=500), nullable=False)
    pid = db.Column(db.Integer, nullable=False)
    run_dir = db.Column(db.Text)
    job_id = db.Column(db.Integer, db.ForeignKey('delayed_job.id'), nullable=False)


class DelayedJob(db.Model):
    id = db.Column(db.String(length=60), primary_key=True)
    type = db.Column(db.Enum(JobTypes))
    status = db.Column(db.Enum(JobStatuses), default=JobStatuses.CREATED)
    status_comment = db.Column(db.String)  # a comment about the status, for example 'Compressing file'
    progress = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    started_at = db.Column(db.DateTime)
    finished_at = db.Column(db.DateTime)
    run_dir_path = db.Column(db.Text)
    output_dir_path = db.Column(db.Text)
    output_file_path = db.Column(db.Text)
    log = db.Column(db.Text)
    raw_params = db.Column(db.Text)
    expires_at = db.Column(db.DateTime)
    api_initial_url = db.Column(db.Text)
    timezone = db.Column(db.String(length=60), default=str(datetime.timezone.utc))
    executions = db.relationship('JobExecution', backref='delayed_job', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<DelayedJob ${self.id} ${self.type} ${self.status}>'

    def public_dict(self):
        """
        Returns a dictionary representation of the object with all the fields that are safe to be public
        :return:
        """
        return {key:str(getattr(self, key)) for key in ['id', 'type', 'status', 'status_comment', 'progress',
                                                        'created_at', 'started_at', 'finished_at', 'output_file_path',
                                                        'raw_params', 'expires_at', 'api_initial_url', 'timezone']}

    def update_run_status(self, new_value):
        old_value = self.status
        if old_value != new_value:
            if new_value == str(JobStatuses.RUNNING):
                self.started_at = datetime.datetime.utcnow()
            elif new_value == str(JobStatuses.FINISHED):
                self.finished_at = datetime.datetime.utcnow()
                self.expires_at = datetime.datetime.utcnow() + datetime.timedelta(days=DAYS_TO_LIVE)

            self.status = new_value

    def get_executions_count(self):
        return len(self.executions)


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


def get_job_by_id(id):

    job = DelayedJob.query.filter_by(id=id).first()
    if job is None:
        raise JobNotFoundError()
    return job


def get_job_by_params(job_type, job_params):

    id = generate_job_id(job_type, job_params)
    return get_job_by_id(id)


def update_job_status(id, new_data):

    job = get_job_by_id(id)
    for key in new_data.keys():

        new_value = new_data.get(key)

        if new_value is not None:
            if key == 'status':
                job.update_run_status(new_value)
            else:
                setattr(job, key, new_value)

    db.session.commit()
    return job


def add_job_execution_to_job(job, execution):

    job.executions.append(execution)
    db.session.add(execution)
    db.session.commit()


def save_job(job):

    db.session.add(job)
    db.session.commit()


def delete_job(job):

    db.session.delete(job)
    db.session.commit()


def delete_all_jobs():

    DelayedJob.query.filter_by().delete()


def delete_all_expired_jobs():

    now = datetime.datetime.utcnow()
    jobs_to_delete = DelayedJob.query.filter(DelayedJob.expires_at < now)
    num_deleted = 0
    for job in jobs_to_delete:
        run_dir_path = job.run_dir_path
        delete_job(job)
        shutil.rmtree(run_dir_path, ignore_errors=True)
        num_deleted += 1

    return num_deleted

