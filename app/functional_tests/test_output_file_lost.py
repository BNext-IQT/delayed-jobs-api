import requests
import time
import datetime


def run_test(server_base_url):

    print('------------------------------------------------------------------------------------------------')
    print('Going to test the lost of a results file')
    print('------------------------------------------------------------------------------------------------')

    submit_url = f'{server_base_url}/submit/test_job/'
    print('submit_url: ', submit_url)
    seconds = 1
    payload = {
        'instruction': 'DELETE_OUTPUT_FILE',
        'seconds': seconds
    }

    print('payload: ', payload)
    submit_request = requests.post(submit_url, json=payload)
    submit_response = submit_request.json()
    job_id = submit_response.get('id')

    print('Waiting until job finishes')
    time.sleep(seconds + 1)
    print('submit_response')

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

    assert started_at_0 != started_at_1, 'The job must have started again'
