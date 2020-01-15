"""
WSGI config for the DelayedJobs server.
"""
from app import create_app

FLASK_APP = create_app()
