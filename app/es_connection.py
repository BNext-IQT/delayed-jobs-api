from elasticsearch import Elasticsearch
from app.config import RUN_CONFIG
es = Elasticsearch([RUN_CONFIG.get('elasticsearch').get('host')])
