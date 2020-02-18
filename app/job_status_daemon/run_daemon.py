#!/usr/bin/env python3
"""
Script that runs the daemon that checks for the job status
"""
import time

from app.job_status_daemon import daemon
from app import create_app

def run():

    flask_app = create_app()
    with flask_app.app_context():
        while True:
            daemon.check_jobs_status()
            time.sleep(1)

if __name__ == "__main__":
    run()