import datetime
import getpass
import socket
import requests
from enum import Enum


class Statuses(Enum):
    """
    Possible Statuses
    """
    RUNNING = 'RUNNING'
    ERROR = 'ERROR'
    FINISHED = 'FINISHED'

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name


class ServerConnection:
    """
    Class that encapsulates job util functions
    """
    current_log = ''

    def __init__(self, server_base_url, job_token, verbose=False):
        """
        Constructor of the class, allows to create a connection object with the parameters provided
        :param server_base_url: base url of the server receiving the reports
        :param job_token: token to authorise the update of the job status
        :param verbose: tells me if you want me to print thinks as I do them.
        """

        self.server_base_url = server_base_url
        self.job_token = job_token
        self.verbose = verbose

    def log(self, msg):
        """
        Same a message to the log
        :param msg: log message to save
        """
        username = getpass.getuser()
        hostname = socket.gethostname()

        full_msg = f'{username}@{hostname} [{datetime.datetime.utcnow()}]: {msg}\n'

        self.current_log += full_msg

        if self.verbose:
            print(full_msg)

        appended_status = {
            'log': self.current_log
        }
        self.send_status_update(appended_status)

    def update_api_initial_url(self, api_initial_url):
        """
        Update's the job's api initial url
        :param api_initial_url: the initial url from where the job is loading its results
        """
        if self.verbose:
            print('--------------------------------------------------------------------------------------')
            print('update_job_output_path: ', api_initial_url)
            print('--------------------------------------------------------------------------------------')

        appended_status = {
            'api_initial_url': api_initial_url
        }
        self.send_status_update(appended_status)

    def update_job_output_path(self, file_path):
        """
        Update's the job output file path
        :param file_path: the file path where the output is
        """
        if self.verbose:
            print('--------------------------------------------------------------------------------------')
            print('update_job_output_path: ', file_path)
            print('--------------------------------------------------------------------------------------')

        appended_status = {
            'output_file_path': file_path
        }
        self.send_status_update(appended_status)

    def update_job_progress(self, progress_percentage):
        """
        Updates the job's progress percentage with the one given as parameter
        :param progress_percentage: current progress percentage
        :param verbose: if you want me to print a verbose output
        :return:
        """
        if self.verbose:
            print('--------------------------------------------------------------------------------------')
            print('Setting progress percentage to', progress_percentage)
            print('--------------------------------------------------------------------------------------')

        appended_status = {
            'progress': progress_percentage
        }
        self.send_status_update(appended_status)

    def update_job_status(self, new_status, status_comment=None):
        """
        Updates the job status
        :param new_status: new status that you want to save
        :param status_comment: a comment on the status. E.g. 'Loading ids'
        :return:
        """
        if self.verbose:
            print('--------------------------------------------------------------------------------------')
            print('Setting status to', str(new_status))
            print('--------------------------------------------------------------------------------------')

        appended_status = {
            'status': new_status,
            'status_comment': status_comment
        }

        self.send_status_update(appended_status)

    def send_status_update(self, appended_status, verbose=False):
        """
        Sends the new status to the server via PATCH
        :param appended_status: dict with the new status to send
        :param verbose: if you want me to print a verbose output
        """
        url = self.server_base_url
        job_token = self.job_token
        headers = {
            'X-Job-Key': job_token
        }
        payload = appended_status

        if verbose:
            print('--------------------------------------------------------------------------------------')
            print('Sending status update')
            print('url: ', url)
            print('headers: ', headers)
            print('payload: ', payload)

        r = requests.patch(url, payload, headers=headers)

        if verbose:
            print('Server response: ', r.status_code)
            print('--------------------------------------------------------------------------------------')