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
    dl__ignore_cache = fields.Boolean(required=True)


class StructureSearchJobSchema(Schema):
    """
    Class that defines the schema for the Structure Search job
    """
    search_type = fields.String(required=True, validate=validate.OneOf(['SIMILARITY', 'SUBSTRUCTURE', 'CONNECTIVITY']))
    search_term = fields.String(required=True)
    threshold = fields.String()
    dl__ignore_cache = fields.Boolean(required=True)


class BiologicalSequenceSearchJobSchema(Schema):
    """
    Class that defines the schema for the Biological Sequence Search job
    """
    sequence = fields.String(required=True)
    matrix = fields.String(validate=validate.OneOf(
        ['BLOSUM45', 'BLOSUM50', 'BLOSUM62', 'BLOSUM80', 'BLOSUM90', 'PAM30', 'PAM70', 'PAM250', 'NONE']))
    alignments = fields.Number(validate=validate.Range(min=0, max=512))
    scores = fields.Number(validate=validate.Range(min=0, max=1000))
    exp = fields.String(validate=validate.OneOf(
        ['1e-200', '1e-100', '1e-50', '1e-10', '1e-5', '1e-4', '1e-3', '1e-2', '1e-1', '1.0', '10', '100', '1000']))
    dropoff = fields.Number(validate=validate.Range(min=0, max=10))
    gapopen = fields.Number(validate=validate.Range(min=-1, max=25))
    gapext = fields.Number(validate=validate.Range(min=-1, max=10))
    filter = fields.String(validate=validate.OneOf(['F', 'T']))
    seqrange = fields.String()
    gapalign = fields.Boolean()
    wordsize = fields.Number(validate=validate.Range(min=6, max=28))
