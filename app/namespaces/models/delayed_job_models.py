"""
    Module with the classes related to the job model
"""
import base64
import datetime
import hashlib
import json
import shutil

from enum import Enum
from app.db import DB


DAYS_TO_LIVE = 7  # Days for which the results are kept


# pylint: disable=no-member,too-few-public-methods
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

class InputFile(DB.Model):
    """
        Class that represents an input file that was sent to the job
    """
    id = DB.Column(DB.Integer, primary_key=True)
    internal_path = DB.Column(DB.Text, nullable=False)
    job_id = DB.Column(DB.Integer, DB.ForeignKey('delayed_job.id'), nullable=False)


class OutputFile(DB.Model):
    """
        Class that represents an output file that the job produced.
    """
    id = DB.Column(DB.Integer, primary_key=True)
    internal_path = DB.Column(DB.Text, nullable=False)
    public_url = DB.Column(DB.Text)
    job_id = DB.Column(DB.Integer, DB.ForeignKey('delayed_job.id'), nullable=False)


class DelayedJob(DB.Model):
    """
    Class that represents a delayed job in the database.
    """
    id = DB.Column(DB.String(length=60), primary_key=True)
    type = DB.Column(DB.Enum(JobTypes))
    status = DB.Column(DB.Enum(JobStatuses), default=JobStatuses.CREATED)
    status_log = DB.Column(DB.String)  # a comment about the status, for example 'Compressing file'
    progress = DB.Column(DB.Integer, default=0)
    created_at = DB.Column(DB.DateTime, default=datetime.datetime.utcnow)
    started_at = DB.Column(DB.DateTime)
    finished_at = DB.Column(DB.DateTime)
    run_dir_path = DB.Column(DB.Text)
    output_dir_path = DB.Column(DB.Text)
    raw_params = DB.Column(DB.Text)
    expires_at = DB.Column(DB.DateTime)
    api_initial_url = DB.Column(DB.Text)
    timezone = DB.Column(DB.String(length=60), default=str(datetime.timezone.utc))
    num_failures = DB.Column(DB.Integer, default=0) # How many times the job has failed.
    input_files = DB.relationship('InputFile', backref='delayed_job', lazy=True, cascade='all, delete-orphan')
    output_files = DB.relationship('OutputFile', backref='delayed_job', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<DelayedJob ${self.id} ${self.type} ${self.status}>'

    def public_dict(self):
        """
        Returns a dictionary representation of the object with all the fields that are safe to be public
        :return:
        """
        return {key: str(getattr(self, key)) for key in ['id', 'type', 'status', 'status_comment', 'progress',
                                                         'created_at', 'started_at', 'finished_at', 'output_file_url',
                                                         'raw_params', 'expires_at', 'api_initial_url', 'timezone']}

    def update_run_status(self, new_value):
        """
        Updates the run status of the job, if status switches to running, it calculates started_at. If the status
        switches to running, it calculates finished_at, and expires_at
        :param new_value: new run status
        """
        old_value = self.status
        if str(old_value) != str(new_value):
            if new_value == str(JobStatuses.RUNNING):
                self.started_at = datetime.datetime.utcnow()
            elif new_value == str(JobStatuses.FINISHED):
                self.finished_at = datetime.datetime.utcnow()
                self.expires_at = datetime.datetime.utcnow() + datetime.timedelta(days=DAYS_TO_LIVE)

            self.status = new_value

    def get_executions_count(self):
        """
        :return: how many times a job has been executed
        """
        return len(self.executions)


def generate_job_id(job_type, job_params, input_files_hashes={}):
    """
    Generates a job id from a sha 256 hash of the string version of the job params in base 64
    :param job_type: type of job run
    :param job_params: parameters for the job
    :param input_files_hashes: a dict with the contents of the input files.
    :return: The id that the job must have
'    """

    all_params = {
        **job_params,
        'job_input_files_hashes': {
            **input_files_hashes
        }
    }

    stable_raw_search_params = json.dumps(all_params, sort_keys=True)
    search_params_digest = hashlib.sha256(stable_raw_search_params.encode('utf-8')).digest()
    base64_search_params_digest = base64.b64encode(search_params_digest).decode('utf-8').replace('/', '_').replace(
        '+', '-')

    return '{}-{}'.format(repr(job_type), base64_search_params_digest)


def get_or_create(job_type, job_params):
    """
    Based on the type and the parameters given, returns a job if it exists, if not it creates it and returns it.
    :param job_type: type of job to get or create
    :param job_params: parameters of the job
    :return: the job corresponding to those parameters.
    """
    job_id = generate_job_id(job_type, job_params)

    existing_job = DelayedJob.query.filter_by(id=job_id).first()
    if existing_job is not None:
        return existing_job

    job = DelayedJob(id=job_id, type=job_type, raw_params=json.dumps(job_params))

    DB.session.add(job)
    DB.session.commit()
    return job


def get_job_by_id(job_id):
    """
    :param job_id: id of the job
    :return: job given an id, raises JobNotFoundError if it does not exist
    """
    job = DelayedJob.query.filter_by(id=job_id).first()
    if job is None:
        raise JobNotFoundError()
    return job


def get_job_by_params(job_type, job_params):
    """
    :param job_type: type of the job
    :param job_params: parameters of the job
    :return: job given a type and params, raises JobNotFoundError if it does not exist
    """
    job_id = generate_job_id(job_type, job_params)
    return get_job_by_id(job_id)


def update_job_status(job_id, new_data):
    """
    Updates the job with new data passed in a dict
    :param job_id: id of the job to modify
    :param new_data: a dictionary with the new data for the job
    :return: the job that was modified
    """
    job = get_job_by_id(job_id)
    for key in new_data.keys():

        new_value = new_data.get(key)

        if new_value is not None:
            if key == 'status':
                job.update_run_status(new_value)
            else:
                setattr(job, key, new_value)

    DB.session.commit()
    return job

def add_input_file_to_job(job, input_file):
    """
    Adds an input file to a job and saves the job
    :param job: job object
    :param input_file: input_file object
    """
    job.input_files.append(input_file)
    DB.session.add(input_file)
    DB.session.commit()

def add_output_file_to_job(job, output_file):
    """
    Adds an input file to a job and saves the job
    :param job: job object
    :param input_file: input_file object
    """
    job.output_files.append(output_file)
    DB.session.add(output_file)
    DB.session.commit()


def save_job(job):
    """
    Saves a job to the database, making sure to commit its current status.
    :param job: job to save.
    """
    DB.session.add(job)
    DB.session.commit()


def delete_job(job):
    """
    Deletes a job from the database, making sure to commit the changes.
    :param job: job to delete.
    """
    DB.session.delete(job)
    DB.session.commit()


def delete_all_jobs():
    """
    Deletes all jobs in the database.
    """
    DelayedJob.query.filter_by().delete()


def delete_all_expired_jobs():
    """
    Deletes all the jobs that have expired
    :return: the number of jobs that were deleted.
    """
    now = datetime.datetime.utcnow()
    jobs_to_delete = DelayedJob.query.filter(DelayedJob.expires_at < now)
    num_deleted = 0
    for job in jobs_to_delete:
        run_dir_path = job.run_dir_path
        output_dir_path = job.output_dir_path
        delete_job(job)
        shutil.rmtree(run_dir_path, ignore_errors=True)
        shutil.rmtree(output_dir_path, ignore_errors=True)
        num_deleted += 1

    return num_deleted
