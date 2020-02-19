#!/usr/bin/env bash
set -x
set -e

IDENTITY_FILE=$1

echo "I am going to check the status of the LSF jobs {LSF_JOB_IDS}"

echo 'START_REMOTE_SSH'
ssh {LSF_USER}@{LSF_HOST} -i $IDENTITY_FILE -oStrictHostKeyChecking=no <<ENDSSH
bjobs -json -o "id stat" {LSF_JOB_IDS}
ENDSSH
echo 'FINISH_REMOTE_SSH'