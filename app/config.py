"""
    Module that handles the configuration of the app
"""
import os
import logging
from pathlib import Path
import hashlib
from enum import Enum
import yaml


CUSTOM_CONFIG_FILE_PATH = os.getenv('CONFIG_FILE_PATH')
if CUSTOM_CONFIG_FILE_PATH is not None:
    CONFIG_FILE_PATH = CUSTOM_CONFIG_FILE_PATH
else:
    CONFIG_FILE_PATH = str(Path().absolute()) + '/config.yml'

print('------------------------------------------------------------------------------------------------')
print('CONFIG_FILE_PATH: ', CONFIG_FILE_PATH)
print('------------------------------------------------------------------------------------------------')


class RunEnvs(Enum):
    """
        Class that defines the possible run environments
    """
    DEV = 'DEV'
    TEST = 'TEST'
    STAGING = 'STAGING'
    PROD = 'PROD'

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name


def hash_secret(secret):
    """
    Returns a a digest of a secret you want to store in memory
    :param secret: secret you want to hash
    :return: a sha256 hash of the secret, encoded in hexadecimal
    """

    hashed = hashlib.sha256(secret.encode('UTF-8')).hexdigest()
    return hashed


def verify_secret(prop_name, value):
    """
    Verifies that a value in the current config (hashed) corresponds to the value passed as parameter (unhashed)
    :param prop_name: name of the property in the configuration
    :param value: clear text value of the property.
    :return: True if the value is correct, false otherwise
    """

    hashed = hashlib.sha256(value.encode('UTF-8')).hexdigest()
    has_must_be = RUN_CONFIG.get(prop_name)

    return hashed == has_must_be

print('Loading run config')
try:
    RUN_CONFIG = yaml.load(open(CONFIG_FILE_PATH, 'r'), Loader=yaml.FullLoader)
    print('Run config loaded')
except FileNotFoundError:
    print('Config file not found. Attempting to load config from environment variable DELAYED_JOBS_RAW_CONFIG')
    raw_config = os.getenv('DELAYED_JOBS_RAW_CONFIG')
    print('raw_config: ', raw_config)
    RUN_CONFIG = yaml.load(raw_config, Loader=yaml.FullLoader)


# Load defaults
if not RUN_CONFIG.get('server_public_host'):
    RUN_CONFIG['server_public_host'] = '0.0.0.0:5000'

if not RUN_CONFIG.get('status_update_host'):
    RUN_CONFIG['status_update_host'] = RUN_CONFIG['server_public_host']

if not RUN_CONFIG.get('base_path'):
    RUN_CONFIG['base_path'] = ''

if not RUN_CONFIG.get('outputs_base_path'):
    RUN_CONFIG['outputs_base_path'] = 'outputs'

STATUS_AGENT_CONFIG = RUN_CONFIG.get('status_agent')
if STATUS_AGENT_CONFIG is None:
    RUN_CONFIG['status_agent'] = {
        'lock_validity_seconds': 1,
        'min_sleep_time': 1,
        'max_sleep_time': 2
    }

CACHE_CONFIG = RUN_CONFIG.get('cache_config')
if CACHE_CONFIG is None:
    RUN_CONFIG['cache_config'] = {
        'CACHE_TYPE': 'simple'
    }

RATE_LIMIT_CONFIG = RUN_CONFIG.get('rate_limit', {})
DEFAULT_RATE_LIMIT = {
    'rates': {
        'default_for_all_routes': '3 per second',
        'admin_login': '1 per second',
        'job_submission': '10 per minute',
    }

}
RUN_CONFIG['rate_limit'] = {
    **DEFAULT_RATE_LIMIT,
    **RATE_LIMIT_CONFIG,
}

# Hash keys and passwords
RUN_CONFIG['admin_password'] = hash_secret(RUN_CONFIG.get('admin_password'))

print('RUN CONFIG: ', RUN_CONFIG)
