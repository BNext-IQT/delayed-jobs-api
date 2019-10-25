import requests
import time


def run_test(server_base_url):

    submit_url = f'{server_base_url}/submit/test_job/'
    print('submit_url: ', submit_url)
    seconds = 6
    payload = {
        'instruction': 'RUN_NORMALLY',
        'seconds': seconds
    }

    print('payload: ', payload)

    submit_request = requests.post(submit_url, json=payload)
    assert submit_request.status_code == 200, 'Job could not be submitted!'

    submit_response = submit_request.json()
    job_id = submit_response.get('id')

    print('wait some time until it starts, it should be running...')
    time.sleep(seconds/2)

    status_request = requests.get(f'{server_base_url}/status/{job_id}')
    status_response = status_request.json()

    job_status = status_response.get('status')
    print('job_status: ', job_status)
    print('status_response code: ', status_response)

