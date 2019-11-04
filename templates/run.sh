#!/usr/bin/env bash -ex

pushd {RUN_DIR}
PYTHONPATH=${{PWD}}:
{SCRIPT_TO_EXECUTE} {PARAMS_FILE} -v > out.txt 2>error.txt
popd