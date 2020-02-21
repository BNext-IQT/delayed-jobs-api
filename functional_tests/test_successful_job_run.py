"""
Module that runs a normal simple job and expects it to run correctly.
"""
import time
from pathlib import Path
import os
import shutil

import requests


def run_test(server_base_url):
    """
    Tests that a job can run normally.
    :param server_base_url: base url of the running server. E.g. http://127.0.0.1:5000
    """

    print('------------------------------------------------------------------------------------------------')
    print('Going to test a successful job run')
    print('------------------------------------------------------------------------------------------------')

    tmp_dir = Path().absolute().joinpath('tmp')
    os.makedirs(tmp_dir, exist_ok=True)
    files = {}
    for i in range(0, 2):
        file_name = f'input_{i}.txt'
        test_file_i_path = tmp_dir.joinpath(file_name)
        with open(test_file_i_path, 'wt') as test_file:
            test_file.write(f'this is input file {i}')

        files[file_name] = open(test_file_i_path, 'rb')

    submit_url = f'{server_base_url}/submit/test_job'
    print('submit_url: ', submit_url)
    seconds = 20
    payload = {
        'instruction': 'RUN_NORMALLY',
        'seconds': seconds,
        'api_url': 'https://www.ebi.ac.uk/chembl/api/data/similarity/CN1C(=O)C=C(c2cccc(Cl)c2)c3cc(ccc13)[C@@](N)(c4ccc(Cl)cc4)c5cncn5C/80.json'
    }

    print('payload: ', payload)
    print('files: ', files)

    shutil.rmtree(tmp_dir)

    submit_request = requests.post(submit_url, data=payload, files=files)
    submission_status_code = submit_request.status_code
    print(f'submission_status_code: {submission_status_code}')
    assert submission_status_code == 200, 'Job could not be submitted!'

    submission_response = submit_request.json()
    print('submission_response: ', submission_response)
    job_id = submission_response.get('job_id')

    print('wait some time until it starts, it should be running...')
    time.sleep(10)

    status_url = f'{server_base_url}/status/{job_id}'
    print('status_url: ', status_url)

    status_request = requests.get(status_url)
    status_response = status_request.json()

    job_status = status_response.get('status')
    print(f'job_status: {job_status}')
    assert job_status == 'RUNNING', 'Job seems to not be running!'

    progress = int(status_response.get('progress'))
    print(f'progress:  {progress}')
    assert progress > 0, 'The job progress is not increasing'

    return

    print('wait some time until it should have finished...')
    time.sleep((seconds / 2) + 1)

    status_request = requests.get(f'{server_base_url}/status/{job_id}')
    status_response = status_request.json()

    job_status = status_response.get('status')
    print(f'job_status: {job_status}')
    assert job_status == 'FINISHED', 'Job should have finished already!'

    output_file_url = status_response.get('output_file_url')
    full_output_file_url = f'{server_base_url}{output_file_url}'
    print(f'full_output_file_url: {full_output_file_url}')
    file_request = requests.get(full_output_file_url)
    assert file_request.status_code == 200, 'The results file could not be downloaded!!'
