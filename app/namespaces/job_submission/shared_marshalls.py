from flask_restplus import Namespace, Resource, fields

BASE_SUBMISSION_RESPONSE = Namespace('base').model('Status', {
    'id': fields.String(required=True, description='The job identifier')
})