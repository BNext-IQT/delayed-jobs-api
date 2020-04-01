"""
Tests for the utils module of the delayed jobs models
"""
import unittest

from app.models import utils

class TestModels(unittest.TestCase):
    """
        Class to test the utils module of the delayed jobs models
    """

    def test_gets_filename_from_url(self):
        """
        Tests that returns correctly the filename from the url
        """

        public_url = 'wwwdev.ebi.ac.uk/chembl/interface_api/delayed_jobs/outputs/TEST-dM4LvIO9HKmyuz3mY_7HK9gIIbz6Nu8Ruxn_4znr1DQ=/output_2.txt'
        filename_must_be = 'output_2.txt'
        filename_got = utils.get_filename_from_url(public_url)

        self.assertEqual(filename_must_be, filename_got, msg='The filename is not obtained correctly!')

    def test_gets_sanitised_filename_when_no_collision(self):
        """
        Tests that the sanitised filename is returned correctly when no collision
        """
        output_files_dict = {}
        filename_to_add = 'some_file.txt'

        sanitised_filename_must_be = 'some_file.txt'
        sanitised_filename_got = utils.get_sanitised_filename(output_files_dict, filename_to_add)

        self.assertEqual(sanitised_filename_must_be, sanitised_filename_got,
                         msg='The sanitised filename was not generated correctly!')

    def test_gets_sanitised_filename_when_collision(self):
        """
        Tests that the sanitised filename is returned correctly when collision
        """

        output_files_dict = {
            'some.file.with.collision.txt': 'some_url'
        }

        filename_to_add = 'some.file.with.collision.txt'

        sanitised_filename_must_be = 'some.file.with.collision(1).txt'
        sanitised_filename_got = utils.get_sanitised_filename(output_files_dict, filename_to_add)

        self.assertEqual(sanitised_filename_must_be, sanitised_filename_got,
                         msg='The sanitised filename was not generated correctly!')

    def test_gets_sanitised_filename_when_multiple_collision(self):
        """
        Tests that the sanitised filename is returned correctly when collision
        """

        output_files_dict = {
            'some.file.with.collision.txt': 'some_url',
            'some.file.with.collision(1).txt': 'another_url'
        }

        filename_to_add = 'some.file.with.collision.txt'

        sanitised_filename_must_be = 'some.file.with.collision(2).txt'
        sanitised_filename_got = utils.get_sanitised_filename(output_files_dict, filename_to_add)

        self.assertEqual(sanitised_filename_must_be, sanitised_filename_got,
                         msg='The sanitised filename was not generated correctly!')

    def test_gets_sanitised_filename_when_collision_2(self):
        """
        Tests that the sanitised filename is returned correctly when collision and the filename has no dots
        """

        output_files_dict = {
            'somefilewithcollision': 'some_url'
        }

        filename_to_add = 'somefilewithcollision'

        sanitised_filename_must_be = 'somefilewithcollision(1)'
        sanitised_filename_got = utils.get_sanitised_filename(output_files_dict, filename_to_add)

        self.assertEqual(sanitised_filename_must_be, sanitised_filename_got,
                         msg='The sanitised filename was not generated correctly!')

    def test_gets_sanitised_filename_when_multiple_collision_2(self):
        """
        Tests that the sanitised filename is returned correctly when collision and the filename has no dots
        """

        output_files_dict = {
            'somefilewithcollision': 'some_url',
            'somefilewithcollision(1)': 'another_url'
        }

        filename_to_add = 'somefilewithcollision(1)'

        sanitised_filename_must_be = 'somefilewithcollision(2)'
        sanitised_filename_got = utils.get_sanitised_filename(output_files_dict, filename_to_add)

        self.assertEqual(sanitised_filename_must_be, sanitised_filename_got,
                         msg='The sanitised filename was not generated correctly!')



