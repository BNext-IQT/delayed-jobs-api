"""
Module that handles the connection with elasticsearch
"""
from elasticsearch import Elasticsearch
from app.config import RUN_CONFIG

ES = Elasticsearch(
    [RUN_CONFIG.get('job_statistics', {}).get('elasticsearch').get('host')],
    http_auth=(RUN_CONFIG.get('job_statistics', {}).get('elasticsearch').get('username'),
               RUN_CONFIG.get('job_statistics', {}).get('elasticsearch').get('password')),
    port=RUN_CONFIG.get('job_statistics', {}).get('elasticsearch').get('port')
)