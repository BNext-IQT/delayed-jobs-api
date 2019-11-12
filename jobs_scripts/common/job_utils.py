import datetime
import getpass
import socket
import requests
from enum import Enum
import yaml


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

    def __init__(self, run_params_file, verbose=False, dry_run=False):
        """
        Constructor of the class, allows to create a connection object with the parameters provided
        :param job_status_url: base url of the server receiving the reports
        :param job_token: token to authorise the update of the job status
        :param verbose: tells me if you want me to print thinks as I do them.
        :param dry_run: if true, do not send anything to the server
        """

        run_params = yaml.load(open(run_params_file, 'r'), Loader=yaml.FullLoader)
        self.job_status_url = run_params.get('status_update_endpoint').get('url')
        self.file_upload_url = run_params.get('file_upload_endpoint').get('url')
        self.job_token = run_params.get('job_token')
        self.verbose = verbose
        self.dry_run = dry_run

    def log(self, msg):
        """
        Same a message to the log
        :param msg: log message to save
        """
        username = getpass.getuser()
        hostname = socket.gethostname()

        full_msg = f'{username}@{hostname} [{datetime.datetime.utcnow()}]: {msg}\n'

        self.current_log += full_msg
        self.print_if_verbose(full_msg)

        appended_status = {
            'log': self.current_log
        }
        self.send_status_update(appended_status)

    def update_api_initial_url(self, api_initial_url):
        """
        Update's the job's api initial url
        :param api_initial_url: the initial url from where the job is loading its results
        """
        self.print_if_verbose('--------------------------------------------------------------------------------------')
        self.print_if_verbose('update_api_initial_url: ', api_initial_url)
        self.print_if_verbose('--------------------------------------------------------------------------------------')

        appended_status = {
            'api_initial_url': api_initial_url
        }
        self.send_status_update(appended_status)

    def upload_job_results_file(self, file_path):
        """
        Uploads the results file to the server
        :param file_path: the file path where the output is
        """
        files = {'file': open(file_path, 'rb')}

        url = self.file_upload_url
        job_token = self.job_token
        headers = {
            'X-Job-Key': job_token
        }

        self.print_if_verbose('--------------------------------------------------------------------------------------')
        self.print_if_verbose('update_api_initial_url')
        self.print_if_verbose('url: ', url)
        self.print_if_verbose('headers: ', headers)
        self.print_if_verbose('file_path: ', file_path)

        if self.dry_run:
            self.print_if_verbose('NOT SENDING REQUEST TO THE SERVER (DRY-RUN)')
        else:
            r = requests.post(url, files=files, headers=headers)
            self.print_if_verbose('Server response: ', r.status_code)
            self.print_if_verbose('-----------------------------------------------------------------------------------')

    def update_job_progress(self, progress_percentage):
        """
        Updates the job's progress percentage with the one given as parameter
        :param progress_percentage: current progress percentage
        :param verbose: if you want me to print a verbose output
        :return:
        """
        self.print_if_verbose('--------------------------------------------------------------------------------------')
        self.print_if_verbose('Setting progress percentage to', progress_percentage)
        self.print_if_verbose('--------------------------------------------------------------------------------------')

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
        self.print_if_verbose('--------------------------------------------------------------------------------------')
        self.print_if_verbose('Setting status to', str(new_status))
        self.print_if_verbose('--------------------------------------------------------------------------------------')

        appended_status = {
            'status': new_status,
            'status_comment': status_comment
        }

        self.send_status_update(appended_status)

    def send_status_update(self, appended_status):
        """
        Sends the new status to the server via PATCH
        :param appended_status: dict with the new status to send
        :param verbose: if you want me to print a verbose output
        """
        url = self.job_status_url
        job_token = self.job_token
        headers = {
            'X-Job-Key': job_token
        }
        payload = appended_status

        self.print_if_verbose('--------------------------------------------------------------------------------------')
        self.print_if_verbose('Sending status update')
        self.print_if_verbose('url: ', url)
        self.print_if_verbose('headers: ', headers)
        self.print_if_verbose('payload: ', payload)

        if self.dry_run:
            self.print_if_verbose('NOT SENDING REQUEST TO THE SERVER (DRY-RUN)')
        else:
            r = requests.patch(url, payload, headers=headers)
            self.print_if_verbose('Server response: ', r.status_code)
            self.print_if_verbose('-----------------------------------------------------------------------------------')

    def print_if_verbose(self, *args):
        if self.verbose:
            print(args)
