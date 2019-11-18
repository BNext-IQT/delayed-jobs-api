"""
Module with shared marshalls
"""
from flask_restplus import Namespace, fields

BASE_SUBMISSION_RESPONSE = Namespace('base').model('Status', {
    'id': fields.String(required=True, description='The job identifier')
})
