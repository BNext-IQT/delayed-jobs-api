#!/usr/bin/env python3
"""
    Script that runs the functional tests for the app
"""
import argparse
import func_test_successful_job_run
import func_test_job_cache
import func_test_parallel_job_submission

PARSER = argparse.ArgumentParser()
PARSER.add_argument('server_base_path', help='server base path to run the tests against',
                    default='http://127.0.0.1:5000', nargs='?')
PARSER.add_argument('admin_username', help='Admin username',
                    default='admin', nargs='?')
PARSER.add_argument('admin_password', help='Admin password',
                    default='123456', nargs='?')
ARGS = PARSER.parse_args()


def run():
    """
    Runs all functional tests
    """
    print(f'Running functional tests on {ARGS.server_base_path}')

    for test_module in [func_test_successful_job_run, func_test_job_cache, func_test_parallel_job_submission]:
        test_module.run_test(ARGS.server_base_path, ARGS.admin_username, ARGS.admin_password)

if __name__ == "__main__":
    run()
