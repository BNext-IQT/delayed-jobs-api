#!/bin/bash -ex

IDENTITY_FILE=${1:-'~/.ssh/id_rsa'}

ssh noah-login -i $IDENTITY_FILE <<ENDSSH
bjobs
ENDSSH