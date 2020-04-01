#!/usr/bin/env bash
set -x
PYTHONPATH=$PYTHONPATH:$(pwd) python3 -u app/job_status_daemon/run_daemon.py