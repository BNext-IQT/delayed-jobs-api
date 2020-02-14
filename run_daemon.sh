#!/usr/bin/env bash
set -x
PYTHONPATH=$PYTHONPATH:$(pwd) app/job_status_daemon/run_daemon.py