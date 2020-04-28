"""
Schemas to validate the input of custom statistics endpoint
"""
from marshmallow import Schema, fields, validate

class JobID(Schema):
    """
    Class that the schema for identifying the job
    """
    job_id = fields.String(required=True)

class TestJobStatistics(Schema):
    """
    Class that the schema for saving statistics for the test jobs
    """
    duration = fields.Number(required=True, validate=validate.Range(min=0))

class StructureSearchJobStatistics(Schema):
    """
    Class that the schema for saving statistics for the structure search jobs
    """
    search_type = fields.String(required=True)
    time_taken = fields.Number(required=True, validate=validate.Range(min=0))

class MMVSearchJobStatistics(Schema):
    """
    Class that the schema for saving statistics for the structure search jobs
    """
    num_sequences = fields.Number(required=True, validate=validate.Range(min=0))