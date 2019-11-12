#!/usr/bin/env python3
import test_successful_job_run
import test_job_cache
import test_parallel_job_submission
import test_failing_job
import test_output_file_lost
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('server_base_path', help='server base path to run the tests against',
                    default='http://127.0.0.1:5000', nargs='?')
args = parser.parse_args()


def run():

    for test_module in [test_successful_job_run]:
        test_module.run_test(args.server_base_path)

if __name__ == "__main__":
    run()
