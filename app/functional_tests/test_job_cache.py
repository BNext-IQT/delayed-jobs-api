import requests
import time
import datetime


def run_test(server_base_url):

    print('------------------------------------------------------------------------------------------------')
    print('Going to test the job caching')
    print('------------------------------------------------------------------------------------------------')

    submit_url = f'{server_base_url}/submit/test_job/'
    print('submit_url: ', submit_url)
    seconds = 1
    payload = {
        'instruction': 'RUN_NORMALLY',
        'seconds': seconds
    }

    print('payload: ', payload)
    submit_request = requests.post(submit_url, json=payload)
    submit_response = submit_request.json()
    job_id = submit_response.get('id')

    print('Waiting until job finishes')
    time.sleep(seconds + 1)

    status_request = requests.get(f'{server_base_url}/status/{job_id}')
    status_response = status_request.json()
    started_at_0 = datetime.datetime.strptime(status_response.get('started_at'), '%Y-%m-%d %H:%M:%S.%f')
    timestamp_0 = started_at_0.timestamp()
    print(f'timestamp_0: {timestamp_0}')
    print(f'started_at_0: {started_at_0}')

    print('Now I will submit the same job again')
    submit_request = requests.post(submit_url, json=payload)
    submit_response = submit_request.json()
    job_id = submit_response.get('id')

    print('Waiting until job finishes')
    time.sleep(seconds + 1)

    status_request = requests.get(f'{server_base_url}/status/{job_id}')
    status_response = status_request.json()
    started_at_1 = datetime.datetime.strptime(status_response.get('started_at'), '%Y-%m-%d %H:%M:%S.%f')
    timestamp_1 = started_at_1.timestamp()
    print(f'timestamp_1: {timestamp_1}')
    print(f'started_at_1: {started_at_1}')

    assert started_at_0 == started_at_1, 'The job must have not started again'

    output_file_url = status_response.get('output_file_url')
    full_output_file_url = f'{server_base_url}{output_file_url}'
    print(f'full_output_file_url: {full_output_file_url}')
    file_request = requests.get(full_output_file_url)
    assert file_request.status_code == 200, 'The results file could not be downloaded!!'
