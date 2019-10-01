#!/bin/bash -ex

IDENTITY_FILE=${1:-'~/.ssh/id_rsa'}

ssh cbl_sw@noah-login -i $IDENTITY_FILE -v <<ENDSSH
echo '------'
whoami
bjobs
echo '------'
ENDSSH