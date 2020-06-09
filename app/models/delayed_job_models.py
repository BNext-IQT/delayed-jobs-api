"""
    Module with the classes related to the job model
"""
import base64
import datetime
import hashlib
import json
import shutil
import copy

from sqlalchemy import and_

from enum import Enum
from app.db import DB
from app.models import utils
from app.config import RUN_CONFIG

DAYS_TO_LIVE = 7  # Days for which the results are kept


# pylint: disable=no-member,too-few-public-methods
class JobStatuses(Enum):
    """
        Possible statuses of delayed jobs
    """
    CREATED = 'CREATED'
    QUEUED = 'QUEUED'
    RUNNING = 'RUNNING'
    ERROR = 'ERROR'
    FINISHED = 'FINISHED'
    UNKNOWN = 'UNKNOWN'

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name


# ----------------------------------------------------------------------------------------------------------------------
# Exceptions
# ----------------------------------------------------------------------------------------------------------------------
class JobNotFoundError(Exception):
    """Base class for exceptions."""


class InputFileNotFoundError(Exception):
    """Base class for exceptions."""


class DockerImageNotSet(Exception):
    """Base class for exceptions."""


class JobConfigNotFoundError(Exception):
    """Base class for exceptions."""


# ----------------------------------------------------------------------------------------------------------------------
# Models
# ----------------------------------------------------------------------------------------------------------------------
class DefaultJobConfig(DB.Model):
    """
    Class that represents a default container image for a job type
    """
    job_type = DB.Column(DB.String(length=60), primary_key=True)
    docker_image_url = DB.Column(DB.Text)
    docker_registry_username = DB.Column(DB.Text)  # Username for the container registry (optional)
    docker_registry_password = DB.Column(DB.Text)  # Password for the container registry (optional)
    requirements_script_path = DB.Column(DB.Text)
    custom_config_repo = DB.Column(DB.Text)
    custom_config_username = DB.Column(DB.Text)
    custom_config_password = DB.Column(DB.Text)
    custom_config_branch = DB.Column(DB.Text)
    custom_config_file_path = DB.Column(DB.Text)


class InputFile(DB.Model):
    """
        Class that represents an input file to the job
    """
    id = DB.Column(DB.Integer, primary_key=True)
    input_key = DB.Column(DB.String(length=120))
    internal_path = DB.Column(DB.Text, nullable=False)
    public_url = DB.Column(DB.Text)
    job_id = DB.Column(DB.String(length=120), DB.ForeignKey('delayed_job.id'), nullable=False)


class OutputFile(DB.Model):
    """
        Class that represents an output file that the job produced.
    """
    id = DB.Column(DB.Integer, primary_key=True)
    internal_path = DB.Column(DB.Text, nullable=False)
    public_url = DB.Column(DB.Text)
    job_id = DB.Column(DB.String(length=120), DB.ForeignKey('delayed_job.id'), nullable=False)


class DelayedJob(DB.Model):
    """
    Class that represents a delayed job in the database.
    """
    id = DB.Column(DB.String(length=120), primary_key=True)
    type = DB.Column(DB.String(length=60), DB.ForeignKey('default_job_config.job_type'), nullable=False)
    status = DB.Column(DB.Enum(JobStatuses), default=JobStatuses.CREATED)
    status_log = DB.Column(DB.Text)  # a comment about the status, for example 'Compressing file'
    progress = DB.Column(DB.Integer, default=0)
    created_at = DB.Column(DB.DateTime, default=datetime.datetime.utcnow)
    started_at = DB.Column(DB.DateTime)
    finished_at = DB.Column(DB.DateTime)
    run_dir_path = DB.Column(DB.Text)
    output_dir_path = DB.Column(DB.Text)
    raw_params = DB.Column(DB.Text)
    expires_at = DB.Column(DB.DateTime)
    api_initial_url = DB.Column(DB.Text)
    docker_image_url = DB.Column(DB.Text)
    timezone = DB.Column(DB.String(length=60), default=str(datetime.timezone.utc))
    num_failures = DB.Column(DB.Integer, default=0)  # How many times the job has failed.
    lsf_job_id = DB.Column(DB.Integer)
    lsf_host = DB.Column(DB.Text)
    requirements_parameters_string = DB.Column(DB.Text)
    status_description = DB.Column(DB.Text)
    run_environment = DB.Column(DB.String(length=60))
    input_files = DB.relationship('InputFile', backref='delayed_job', lazy=True, cascade='all, delete-orphan')
    output_files = DB.relationship('OutputFile', backref='delayed_job', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<DelayedJob ${self.id} ${self.type} ${self.status}>'

    def public_dict(self, server_base_url='http://0.0.0.0:5000'):
        """
        Returns a dictionary representation of the object with all the fields that are safe to be public
        :param server_base_url: url to use as base for building the output files urls
        """
        plain_properties = {key: str(getattr(self, key)) for key in ['id', 'type', 'status', 'status_log', 'progress',
                                                                     'created_at', 'started_at', 'finished_at',
                                                                     'raw_params',
                                                                     'expires_at', 'api_initial_url',
                                                                     'docker_image_url',
                                                                     'timezone', 'num_failures', 'status_description']}

        input_files_urls = utils.get_input_files_dict(self.input_files, server_base_url)
        output_files_urls = utils.get_output_files_dict(self.output_files, server_base_url)

        return {
            **plain_properties,
            'input_files_urls': input_files_urls,
            'output_files_urls': output_files_urls
        }

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


# ----------------------------------------------------------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------------------------------------------------------
def generate_job_id(job_type, job_params, docker_image_url, input_files_hashes={}):
    """
    Generates a job id from a sha 256 hash of the string version of the job params in base 64
    :param job_type: type of job run
    :param job_params: parameters for the job
    :param input_files_hashes: a dict with the contents of the input files.
    :return: The id that the job must have
'    """
    parsed_job_params = copy.deepcopy(job_params)
    # Do not take into account cache parameter for job id
    if parsed_job_params.get('dl__ignore_cache') is not None:
        del parsed_job_params['dl__ignore_cache']

    all_params = {
        **parsed_job_params,
        'job_input_files_hashes': {
            **input_files_hashes
        },
        'docker_image_url': docker_image_url
    }

    stable_raw_search_params = json.dumps(all_params, sort_keys=True)
    search_params_digest = hashlib.sha256(stable_raw_search_params.encode('utf-8')).digest()
    base64_search_params_digest = base64.b64encode(search_params_digest).decode('utf-8').replace('/', '_').replace(
        '+', '-')

    return '{}-{}'.format(job_type, base64_search_params_digest)


def get_job_config(job_type):
    """
    returns the job config for the job whose type is received as parameter
    :param job_type: type of job for which get the config
    :return: config object corresponding to the type given
    """
    job_config = DefaultJobConfig.query.filter_by(job_type=job_type).first()
    if job_config is None:
        raise JobConfigNotFoundError(f'No configuration was found for {job_type} jobs')
    return job_config


def get_or_create(job_type, job_params, docker_image_url, input_files_hashes={}):
    """
    Based on the type and the parameters given, returns a job if it exists, if not it creates it and returns it.
    :param job_type: type of job to get or create
    :param job_params: parameters of the job
    :param input_files_hashes:
    :return: the job corresponding to those parameters.
    """
    job_id = generate_job_id(job_type, job_params, docker_image_url, input_files_hashes)

    existing_job = DelayedJob.query.filter_by(id=job_id).first()
    if existing_job is not None:
        return existing_job

    run_environment = RUN_CONFIG.get('run_env')
    job = DelayedJob(id=job_id, type=job_type, raw_params=json.dumps(job_params, sort_keys=True),
                     docker_image_url=docker_image_url, run_environment=run_environment)

    DB.session.add(job)
    DB.session.commit()
    return job


def get_job_by_id(job_id, force_refresh=False):
    """
    returns a job by its id, if the job was found but expired it deletes it (lazy cache) and raises an error
    :param job_id: id of the job
    :param force_refresh: force a refresh on the object
    :return: job given an id, raises JobNotFoundError if it does not exist
    """
    if force_refresh:
        DB.session.commit()
        DB.session.expire_all()

    job = DelayedJob.query.filter_by(id=job_id).first()

    if job is None:
        raise JobNotFoundError(f'The job with id {job_id} does not exist!')

    expiration_date = job.expires_at
    if expiration_date is not None:
        current_time = datetime.datetime.utcnow()
        job_expired = expiration_date < current_time
        if job_expired:
            delete_job(job)
            raise JobNotFoundError(f'The job with id {job_id} does not exist!')

    if force_refresh:
        DB.session.commit()
        DB.session.expire(job)
        DB.session.refresh(job)

    return job


def get_job_input_file(job_id, input_key):
    """
    :param job_id: job id that owns the input file
    :param input_key: input key of the input file
    :return: the input file that belongs to the job whose id is given as parameter, and with the key given as parameter
    """
    belongs_to_job_id = InputFile.job_id == job_id
    input_key_is_this_one = InputFile.input_key == input_key

    input_file = InputFile.query.filter(
        and_(belongs_to_job_id, input_key_is_this_one)
    ).first()

    if input_file is None:
        raise InputFileNotFoundError(f'No input file found for job {job_id} with key {input_key}')

    return input_file


def get_job_by_lsf_id(lsf_job_id):
    """
    :param lsf_job_id: id of the job in the lsf cluster
    :return: job given an lsf id, raises JobNotFoundError if it does not exist
    """
    job = DelayedJob.query.filter_by(lsf_job_id=lsf_job_id).first()
    if job is None:
        raise JobNotFoundError()
    return job


def generate_default_job_configs():
    """
    Generates a default set of job configurations, useful for testing.
    """
    test_job_config = DefaultJobConfig(
        job_type='TEST',
        docker_image_url='docker://dockerhub.ebi.ac.uk/chembl/chembl/delayed-jobs/test-job:8d8ea512-17-Feb-2020--10-43-54'
    )
    DB.session.add(test_job_config)
    DB.session.commit()

    structure_search_job_config = DefaultJobConfig(
        job_type='STRUCTURE_SEARCH',
        docker_image_url='some_url'
    )
    DB.session.add(structure_search_job_config)
    DB.session.commit()

    mmv_job_config = DefaultJobConfig(
        job_type='MMV',
        docker_image_url='docker://dockerhub.ebi.ac.uk/chembl/chembl/delayed-jobs/mmv_job:0b0382da-21-Feb-2020--15-50-32',
        docker_registry_username='some_user',
        docker_registry_password='some_password'
    )

    DB.session.add(mmv_job_config)
    DB.session.commit()

    biological_sequence_search_job_config = DefaultJobConfig(
        job_type='BIOLOGICAL_SEQUENCE_SEARCH',
        docker_image_url='some_url'
    )
    DB.session.add(biological_sequence_search_job_config)
    DB.session.commit()

    download_config = DefaultJobConfig(
        job_type='DOWNLOAD',
        docker_image_url='some_url',
        custom_config_repo='some_repo',
        custom_config_username = 'some_user',
        custom_config_password = 'some_password',
        custom_config_branch = 'some_branch',
        custom_config_file_path = 'config_file_path'
    )
    DB.session.add(download_config)
    DB.session.commit()


def get_docker_image_url(job_type):
    """
    :param job_type: job type for which to get the image url
    :return: the url of the docker image to use for this type of job
    """
    docker_image = DefaultJobConfig.query.filter_by(job_type=job_type).first()

    if docker_image is not None:
        return docker_image.docker_image_url
    else:
        raise DockerImageNotSet(f'There is no image container url set for jobs of type {job_type}')


def get_job_by_params(job_type, job_params, docker_image_url, input_files_hashes={}):
    """
    :param job_type: type of the job
    :param job_params: parameters of the job
    :param docker_image_url: docker image used for the job
    :param input_files_hashes:dict of  hashes of the input files of the job
    :return: job given a type and params, raises JobNotFoundError if it does not exist
    """
    job_id = generate_job_id(job_type, job_params, docker_image_url, input_files_hashes)
    return get_job_by_id(job_id)


def update_job_progress(job_id, progress, status_log, status_description):
    """
    Updates the job with new data passed in a dict
    :param job_id: id of the job to modify
    :param progress: progress percentage of the job
    :return: the job that was modified
    """
    job = get_job_by_id(job_id)

    job.progress = progress

    if status_log is not None:
        if job.status_log is None:
            job.status_log = ''
        job.status_log += f'{datetime.datetime.now().isoformat()}: {status_log}\n'

    if status_description is not None:
        job.status_description = status_description

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
    DB.session.commit()


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


def delete_all_jobs_by_type(job_type):
    """
    Deletes all the jobs that have expired
    :return: the number of jobs that were deleted.
    """
    jobs_to_delete = DelayedJob.query.filter_by(type=job_type)
    num_deleted = 0
    for job in jobs_to_delete:
        run_dir_path = job.run_dir_path
        output_dir_path = job.output_dir_path
        delete_job(job)
        shutil.rmtree(run_dir_path, ignore_errors=True)
        shutil.rmtree(output_dir_path, ignore_errors=True)
        num_deleted += 1

    return num_deleted


def get_lsf_job_ids_to_check(lsf_host):
    """
    :param lsf_host: lsf host for which to return the jobs to check
    :return: a list of LSF job IDs for which it is necessary check the status in the LSF cluster. The jobs that are
    checked are the ones that:
    1. Were submitted to the same LSF cluster that I am running with (defined in configuration)
    2. Are not in Error or Finished state.
    """

    DB.session.commit()

    status_is_not_error_or_finished = DelayedJob.status.notin_(
        [JobStatuses.ERROR, JobStatuses.FINISHED]
    )

    lsf_host_is_my_host = DelayedJob.lsf_host == lsf_host

    current_run_environment = RUN_CONFIG.get('run_env')
    run_environment_is_my_current_environment = \
        DelayedJob.run_environment == current_run_environment

    job_to_check_status = DelayedJob.query.filter(
        and_(lsf_host_is_my_host, status_is_not_error_or_finished, run_environment_is_my_current_environment)
    )

    # Make sure there are no None value. This can happen when the server has created a job and is submitting it, and the
    # same time the daemon asks for jobs to check. This makes the daemon crash.
    ids = [job.lsf_job_id for job in job_to_check_status if job.lsf_job_id is not None]

    DB.session.commit()

    return ids


def add_output_to_job(job, internal_path, public_url):
    """
    Adds an output to the job given as a parameter
    :param job: job for which to add the output file
    :param internal_path: internal absolute path of the output file
    :param public_url: public url to access the file
    """
    output_file = OutputFile(
        internal_path=internal_path,
        public_url=public_url
    )
    job.output_files.append(output_file)
    save_job(job)
