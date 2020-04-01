"""
Schemas to validate the input of the administrative tasks
"""
from marshmallow import Schema, fields

class DeleteAllJobsByTypeOperation(Schema):
    """
    Class that defines the schema of the operation that deletes all jobs by type
    """
    job_type = fields.String(required=True)

class DeleteAllOutputsOfJobOperation(Schema):
    """
    Class that defines the schema of the operation that deletes the outputs of a job by id
    """
    job_id = fields.String(required=True)