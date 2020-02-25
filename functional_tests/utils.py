"""
Module with utils functions for the functional tests
"""
import os

def prepare_test_job_1(tmp_dir):
    """
    create some inputs, some parameters for a test job
    :return: a dict with the test job properties
    """

    os.makedirs(tmp_dir, exist_ok=True)
    files = {}
    for i in range(0, 2):
        file_name = f'input_{i}.txt'
        test_file_i_path = tmp_dir.joinpath(file_name)
        with open(test_file_i_path, 'wt') as test_file:
            test_file.write(f'this is input file {i}')

        files[file_name] = open(test_file_i_path, 'rb')

    seconds = 20
    payload = {
        'instruction': 'RUN_NORMALLY',
        'seconds': seconds,
        'api_url': 'https://www.ebi.ac.uk/chembl/api/data/similarity/CN1C(=O)C=C(c2cccc(Cl)c2)c3cc(ccc13)[C@@](N)(c4ccc(Cl)cc4)c5cncn5C/80.json',
        'dl__ignore_cache': True
    }

    print('payload: ', payload)
    print('files: ', files)

    return {
        'payload': payload,
        'files': files
    }

def get_submit_url(server_base_url):
    """
    :param server_base_url: the base url of the server
    :return: the url used to submit jobs
    """
    return f'{server_base_url}/submit/test_job'