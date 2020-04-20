"""
Schemas to validate the input of job status Endpoint
"""
from marshmallow import Schema, fields, validate

class JobStatus(Schema):
    """
    Class that the schema for getting a job status job by id
    """
    job_id = fields.String(required=True)

class JobInputFileRequest(Schema):
    """
    Class that the schema for getting a the input file of a job
    """
    job_id = fields.String(required=True)
    input_path = fields.String(required=True)

class JobStatusUpdate(Schema):
    """
    Class that the schema for updating a job status job by id
    """
    progress = fields.Number(required=True, validate=validate.Range(min=0, max=100))
    status_log = fields.String()
    status_description = fields.String()

