import os
import yaml
from pathlib import Path

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

RUN_CONFIG = yaml.load(open(CONFIG_FILE_PATH, 'r'), Loader=yaml.FullLoader)
