"""
    Module with the classes related to the job model
"""
import json
import hashlib
import base64
from enum import Enum

from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()
from sqlalchemy import Column, Integer, String

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine('sqlite:///:memory:', echo=True)

Session = sessionmaker(bind=engine)
session = Session()


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


class DelayedJobModel(Base):
    __tablename__ = 'delayed_job'
    id = Column(String, primary_key=True)


def generate_job_id(job_type, job_params):
    """
    Generates a job id from a sha 256 hash of the string version of the job params in base 64
    :param job_type: type of job run
    :param job_params: parameters for the job
    :return: The id that the job must have
    """

    stable_raw_search_params = json.dumps(job_params, sort_keys=True)
    search_params_digest = hashlib.sha256(stable_raw_search_params.encode('utf-8')).digest()
    base64_search_params_digest = base64.b64encode(search_params_digest).decode('utf-8').replace('/', '_').replace(
        '+', '-')

    return '{}-{}'.format(repr(job_type), base64_search_params_digest)


# TODO test this
def get_or_create(job_type, job_params):

    print('Getting or creating job!!!')
    id = generate_job_id(job_type, job_params)
    print('id: ', id)
    job = DelayedJobModel(id=id)
    print('job: ', job)
    session.add(job)
    session.commit()
    return job

Base.metadata.create_all(engine, Base.metadata.tables.values(), checkfirst=True)
