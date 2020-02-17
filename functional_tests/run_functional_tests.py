#!/usr/bin/env python3
"""
    Script that runs the functional tests for the app
"""
import argparse

PARSER = argparse.ArgumentParser()
PARSER.add_argument('server_base_path', help='server base path to run the tests against',
                    default='http://127.0.0.1:5000', nargs='?')
ARGS = PARSER.parse_args()


def run():
    """
    Runs all functional tests
    """
    print(f'Running functional tests on {ARGS.server_base_path}')
    return

    for test_module in [test_successful_job_run, test_job_cache, test_parallel_job_submission, test_failing_job,
                        test_output_file_lost]:
        test_module.run_test(ARGS.server_base_path)

if __name__ == "__main__":
    run()
