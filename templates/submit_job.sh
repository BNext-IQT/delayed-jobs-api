#!/usr/bin/env bash
set -x
set -e

IDENTITY_FILE=$1

echo "I am going to submit the job {JOB_ID}"

ssh {LSF_USER}@{LSF_HOST} -i $IDENTITY_FILE -oStrictHostKeyChecking=no <<ENDSSH
bsub "singularity exec {DOCKER_IMAGE_URL} /app/run_job.sh {RUN_PARAMS_FILE}"
ENDSSH
