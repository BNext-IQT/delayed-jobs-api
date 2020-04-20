"""
    Module with utils function for the delayed job models
"""
import re
from app.config import RUN_CONFIG

def get_input_files_dict(input_files, server_base_url):
    """
    :param input_files: the list of InputFile objects of the job
    :param server_base_url: the server base url to build the urls from it
    :return: a dict describing the input files of a job. To be used for generating
    a public dict describing a job
    """
    input_files_dict = {}
    for input_file in input_files:

        if server_base_url.endswith('/'):
            public_url = f'{server_base_url[:-1]}{RUN_CONFIG.get("base_path")}{input_file.public_url}'
        else:
            public_url = f'{server_base_url}{RUN_CONFIG.get("base_path")}{input_file.public_url}'

        input_files_dict[input_file.input_key] = public_url

    return input_files_dict


def get_output_files_dict(output_files, server_base_url):
    """
    :param output_files: the list of OutputFile objects of the job
    :param server_base_url: the server base url to build the urls from it
    :return: a dict describing the output files of a job. To be used for generating
    a public dict describing a job
    """

    output_files_dict = {}
    for output_file in output_files:

        if server_base_url.endswith('/'):
            public_url = f'{server_base_url[:-1]}{output_file.public_url}'
        else:
            public_url = f'{server_base_url}{output_file.public_url}'

        filename = get_filename_from_url(public_url)
        sanitised_filename = get_sanitised_filename(output_files_dict, filename)
        output_files_dict[sanitised_filename] = public_url

    return output_files_dict

def get_filename_from_url(public_url):
    """
    :param public_url: public url of the output file
    :return: Given a public url, returns the filename only. For example:
    from wwwdev.ebi.ac.uk/chembl/interface_api/delayed_jobs/outputs/TEST-dM4LvIO9HKmyuz3mY_7HK9gIIbz6Nu8Ruxn_4znr1DQ=/output_2.txt
    returns output_2.txt
    """

    url_parts = public_url.split('/')
    return url_parts[-1]

def get_sanitised_filename(output_files_dict, filename_to_add):
    """
    :param output_files_dict: dictionary with the output files and their urls
    :param filename_to_add: filename to add to the dict
    :return: a filename that will not collide with previously existing keys
    """

    key_already_exists = output_files_dict.get(filename_to_add) is not None
    sanitised_filename = filename_to_add
    i = 1
    while key_already_exists:

        if '.' in sanitised_filename:
            file_extension = sanitised_filename.split('.')[-1]
            if re.match(r'.*\(\d+\)\.\w+$', sanitised_filename):
                sanitised_filename = re.sub(r'\(\d+\)\.\w+$', f'({i}).{file_extension}', sanitised_filename)
            else:
                filename_parts = sanitised_filename.split('.')
                sanitised_filename = f'{".".join(filename_parts[:-1])}({i}).{file_extension}'
        else:
            if re.match(r'.*\(\d+\)$', sanitised_filename):
                sanitised_filename = re.sub(r'\(\d\)$', f'({i})', sanitised_filename)
            else:
                sanitised_filename = f'{sanitised_filename}({i})'

        key_already_exists = output_files_dict.get(sanitised_filename) is not None


        i += 1


    return sanitised_filename