"""
Tests for the search statistics API
"""
from pathlib import Path
import unittest
import os

from jobs_scripts.common.es.file_generator import FileGenerator


OUTPUT_DIR_PATH = str(Path().absolute()) + '/test_output'


def get_sawed_off_file_writer_normal_props():
    """
    :return: a file writer with basic columns to download
    """
    test_columns_to_download = [{'label': 'ChEMBL ID', 'prop_id': 'molecule_chembl_id'},
                                {'label': 'Name', 'prop_id': 'pref_name'}]

    file_generator = FileGenerator()
    file_generator.set_columns_to_download(test_columns_to_download)
    return file_generator


def get_sawed_off_file_writer_virtual_props():
    """
    :return: a file writer with basic columns to download
    """
    test_columns_to_download = [{'label': 'ChEMBL ID', 'prop_id': 'molecule_chembl_id'},
                                {'label': 'Research Codes', 'prop_id': 'research_codes', 'is_virtual': True,
                                 'is_contextual': True, 'based_on': 'molecule_synonyms'}]

    file_generator = FileGenerator()
    file_generator.set_columns_to_download(test_columns_to_download)
    return file_generator


def get_full_writer_no_parsing_required():
    """
    :return: a writer with the full configuration, where no parsing is required
    """

    test_columns_to_download = [{'label': 'ChEMBL ID', 'prop_id': 'molecule_chembl_id'},
                                {'label': 'Name', 'prop_id': 'pref_name'}]
    test_index_name = 'chembl_molecule'
    test_query = {
        "query_string": {
            "query": "molecule_chembl_id:(CHEMBL59)"
        }
    }
    test_filename = 'test' + str(int(round(time.time() * 1000)))

    file_generator = FileGenerator()
    file_generator.set_columns_to_download(test_columns_to_download)
    file_generator.set_index_name(test_index_name)
    file_generator.set_query(test_query)


# pylint: disable=too-many-locals,no-member
class FileWriterTester(unittest.TestCase):
    """
    Class that tests the File Writer
    """

    def setUp(self):
        os.makedirs(OUTPUT_DIR_PATH, exist_ok=True)

    def tearDown(self):
        os.remove(OUTPUT_DIR_PATH)

    def test_generates_source(self):
        """
        Tests that the source part of the query is generated correctly
        """
        file_generator = get_sawed_off_file_writer_normal_props()

        source_must_be = ['molecule_chembl_id', 'pref_name']
        source_got = file_generator.get_search_source()
        self.assertEqual(source_must_be, source_got, 'The search source is not generated correctly')

    def test_generates_source_for_virtual_properties(self):
        """
        Tests that the source part of the query is generated correctly with virtual properties
        """
        file_generator = get_sawed_off_file_writer_virtual_props()
        source_must_be = ['molecule_chembl_id', 'molecule_synonyms']

        source_got = file_generator.get_search_source()
        self.assertEqual(source_must_be, source_got, 'The search source is not generated correctly')

    def test_fails_when_output_format_is_not_available(self):
        """
        Tests that the file generator file fails when requested an output that is not available
        """

        file_generator = get_sawed_off_file_writer_normal_props()
        with self.assertRaises(file_generator.FileGeneratorError,
                               msg='It should raise an error when the given format is not supported'):

            file_generator.set_output_format('XLSX')

    def test_fails_when_index_name_is_not_provided(self):
        """
        Test fails when no index name is provided
        """
        file_generator = get_sawed_off_file_writer_virtual_props()
        test_index_name = None

        with self.assertRaises(file_generator.FileGeneratorError,
                               msg='It should raise an error when the index name is not given'):
            file_generator.set_index_name(test_index_name)

    def test_downloads_and_writes_csv_file_no_parsing_required(self):
        """
        Tests that it can download the data and write a csv file when no parsing is required
        """

        return
        test_columns_to_download = [{'label': 'ChEMBL ID', 'prop_id': 'molecule_chembl_id'},
                                    {'label': 'Name', 'prop_id': 'pref_name'}]
        test_index_name = 'chembl_molecule'
        query_file_path = os.path.join(settings.GLADOS_ROOT, 'es/tests/data/test_query0.json')
        test_query = json.loads(open(query_file_path, 'r').read())

        filename = 'test' + str(int(round(time.time() * 1000)))
        out_file_path, total_items = file_generator.write_separated_values_file(
            desired_format=file_generator.OutputFormats.CSV,
            index_name=test_index_name, query=test_query,
            columns_to_download=test_columns_to_download,
            base_file_name=filename)

        with gzip.open(out_file_path, 'rt') as file_got:
            lines_got = file_got.readlines()
            line_0 = lines_got[0]
            self.assertEqual(line_0, '"ChEMBL ID";"Name"\n', 'Header line is malformed!')
            line_1 = lines_got[1]
            self.assertEqual(line_1, '"CHEMBL59";"DOPAMINE"\n', 'Line is malformed!')
