#!/usr/bin/env python3
"""
    Script that runs requests the deletion of expired jobs
"""
import argparse

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
    Runs the script
    """
    print(f'Requesting deletion of expired jobs on {ARGS.server_base_path}')

if __name__ == "__main__":
    run()