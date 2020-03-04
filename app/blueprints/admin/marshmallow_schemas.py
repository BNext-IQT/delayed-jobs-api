"""
Schemas to validate the input of the administrative tasks
"""
from marshmallow import Schema, fields, validate

class DeleteAllJobsByTypeOperation(Schema):
    """
    Class that defines the schema of the operation that deletes all jobs by type
    """
    job_type = fields.String(required=True)