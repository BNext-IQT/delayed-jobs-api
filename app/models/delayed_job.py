"""
    Module with the classes related to the job model
"""
from enum import Enum

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


# TODO
def generate_job_id(job_type, job_params):
    return '123'


# TODO test this
def get_or_create(job_type, job_params):

    print('Getting or creating job!!!')
