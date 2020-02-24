#!/usr/bin/env bash
set -x
set -e

IDENTITY_FILE=$1

echo "I am going to submit the job {JOB_ID}"

ssh {LSF_USER}@{LSF_HOST} -i $IDENTITY_FILE -oStrictHostKeyChecking=no <<ENDSSH

USE_DOCKER_REGISTRY_CREDENTIALS={USE_DOCKER_REGISTRY_CREDENTIALS}
if [ "$USE_DOCKER_REGISTRY_CREDENTIALS" = true ];
then
    export SINGULARITY_DOCKER_USERNAME='{DOCKER_REGISTRY_USERNAME}'
    export SINGULARITY_DOCKER_PASSWORD='{DOCKER_REGISTRY_PASSWORD}'
fi
bsub -J {JOB_ID} -o {RUN_DIR}/job_run.out -e {RUN_DIR}/job_run.err "singularity exec {DOCKER_IMAGE_URL} /app/run_job.sh {RUN_PARAMS_FILE}"
ENDSSH
