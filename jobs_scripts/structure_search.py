#!/usr/bin/env python3

import argparse

parser = argparse.ArgumentParser()
parser.add_argument('run_params_file', help='The path of the file with the run params')
parser.add_argument('-v', '--verbose', help='Make output verbose', action="store_true")
args = parser.parse_args()

RUN_PARAMS = {}
LOG = ''


def run(run_params_file, be_verbose):
    print('RUNNING...')
    print('run_params_file: ', run_params_file)
    print('be_verbose: ', be_verbose)


if __name__ == "__main__":
    run(args.run_params_file, args.verbose)
