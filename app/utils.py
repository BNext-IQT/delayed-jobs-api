"""
    Module with utils functions for all the modules in the app
"""
import shutil
import subprocess

import app.app_logging as app_logging
from app.errors import DelayedJobsError

def delete_directory_robustly(dir_path):
    """
    Deletes a directory in a more robust way, if it catches and exception tries other methods
    :param dir_path: path of the directory to delete
    """
    try:
        shutil.rmtree(dir_path)
    except OSError as error:
        app_logging.debug(f'Error got while deleting {dir_path}')
        app_logging.debug(str(error))
        app_logging.debug(f'Falling back to shell command')

        delete_command = f'rm -rf {dir_path}'

        deletion_process = subprocess.run(delete_command.split(' '), stdout=subprocess.PIPE,
                                                     stderr=subprocess.PIPE)

        return_code = deletion_process.returncode
        app_logging.debug(f'deletion return code was: {return_code}')

        if return_code != 0:
            raise DelayedJobsError(f'There was an error when deleting the dir {dir_path}, please check the logs')

        app_logging.debug(f'Deletion stdout: \n {deletion_process.stdout}')
        app_logging.debug(f'Deletion stderr: \n {deletion_process.stderr}')
