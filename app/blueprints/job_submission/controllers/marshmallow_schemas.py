"""
This module defines the schemas to validate the inputs of the submissions controller
"""
from marshmallow import Schema, fields, validate

class TestJobSchema(Schema):
    """
    Class that defines the schema for the test job
    """
    instruction = fields.String(required=True, validate=validate.OneOf(['RUN_NORMALLY', 'FAIL']))
    seconds = fields.Number(required=True, validate=validate.Range(min=0, max=512))
    api_url = fields.String(required=True)
    dl__ignore_cache = fields.Boolean(required=True)

class MMVJobSchema(Schema):
    """
    Class that defines the schema for the MMV job
    """
    standardise = fields.Boolean(required=True)
    dl__ignore_cache =fields.Boolean(required=True)