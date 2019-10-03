"""
    Module with app's models
"""

# pylint: disable=too-few-public-methods
class DelayedJob:
    """
    Model to represent jobs
    """
    SIMILARITY = 'SIMILARITY'
    SUBSTRUCTURE = 'SUBSTRUCTURE'
    CONNECTIVITY = 'CONNECTIVITY'
    BLAST = 'BLAST'
    DOWNLOAD = 'DOWNLOAD'
