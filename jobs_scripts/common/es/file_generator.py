"""
Module that produces files from elasticsearch indexes and queries
"""
from enum import Enum
# ----------------------------------------------------------------------------------------------------------------------
# File Generator
# ----------------------------------------------------------------------------------------------------------------------
class FileGenerator:
    """
    Class that handles the generation of files from elasticsearch
    """

    class OutputFormats(Enum):
        """
        Class that standardises the available file outputs
        """
        CSV = 'CSV'
        TSV = 'TSV'
        SDF = 'SDF'

    class FileGeneratorError(Exception):
        """Base class for exceptions in the file writer."""

    def __init__(self, output_dir_path):

        self.columns_to_download = []
        self.output_format = None
        self.index_name = None
        self.query = None
        self.filename = None
        self.output_dir = output_dir_path

    def set_columns_to_download(self, columns_to_download):

        self.columns_to_download = columns_to_download

    def set_output_format(self, output_format):

        if output_format not in [possible_format.value for possible_format in self.OutputFormats]:
            raise self.FileGeneratorError('Format not supported!')
        self.output_format = output_format

    def set_index_name(self, index_name):

        if index_name is None:
            raise self.FileGeneratorError('index_name is None!')

        self.index_name = index_name

    def set_query(self, query):

        self.query = query

    def set_filename(self, filename):

        self.filename = filename

    def get_search_source(self):
        """
        :param columns_to_download: the list of columns for the download.
        :return: the source section of the query to be sent to elasticsearch
        """

        source = []
        for col in self.columns_to_download:
            prop_name = col.get('prop_id')
            based_on = col.get('based_on')
            if based_on is not None:
                source.append(based_on)
            else:
                source.append(prop_name)

        return source

