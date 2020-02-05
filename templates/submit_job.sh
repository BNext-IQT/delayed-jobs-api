#!/usr/bin/env bash
set -x
set -e

IDENTITY_FILE=$1

echo "I am going to submit the job {JOB_ID}"

ssh {LSF_USER}@{LSF_HOST} -i $IDENTITY_FILE -v -oStrictHostKeyChecking=no <<ENDSSH
echo '------'
whoami
bjobs
echo '------'
ENDSSH
