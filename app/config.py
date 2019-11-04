import os
import yaml
from pathlib import Path
import hashlib

CUSTOM_CONFIG_FILE_PATH = os.getenv('CONFIG_FILE_PATH')
if CUSTOM_CONFIG_FILE_PATH is not None:
    CONFIG_FILE_PATH = CUSTOM_CONFIG_FILE_PATH
else:
    CONFIG_FILE_PATH = str(Path().absolute()) + '/config.yml'

print('------------------------------------------------------------------------------------------------')
print('CONFIG_FILE_PATH: ', CONFIG_FILE_PATH)
print('------------------------------------------------------------------------------------------------')


class RunEnvs(object):
    DEV = 'DEV'
    TEST = 'TEST'
    STAGING = 'STAGING'
    PROD = 'PROD'


def hash_secret(secret):

    hashed = hashlib.sha256(secret.encode('UTF-8')).hexdigest()
    return hashed


def verify_secret(prop_name, value):

    hashed = hashlib.sha256(value.encode('UTF-8')).hexdigest()
    has_must_be = RUN_CONFIG.get(prop_name)

    return hashed == has_must_be

RUN_CONFIG = yaml.load(open(CONFIG_FILE_PATH, 'r'), Loader=yaml.FullLoader)

# Hash keys and passwords
RUN_CONFIG['admin_password'] = hash_secret(RUN_CONFIG.get('admin_password'))

