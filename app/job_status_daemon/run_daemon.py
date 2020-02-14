#!/usr/bin/env python3
"""
Script that runs the daemon that checks for the job status
"""
import time

def run():

    while True:
        print('I am the daemon...')
        time.sleep(1)

if __name__ == "__main__":
    run()