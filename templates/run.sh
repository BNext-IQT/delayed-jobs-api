#!/usr/bin/env bash

set -o verbose
set -e

pushd {RUN_DIR}
PYTHONPATH=${{PWD}}:
{SCRIPT_TO_EXECUTE} {PARAMS_FILE} -v > out.txt 2>error.txt
popd