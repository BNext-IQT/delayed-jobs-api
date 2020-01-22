#!/usr/bin/env python3
"""
Script that generates a configmap yaml file from a raw config string with the run config
"""
import argparse

PARSER = argparse.ArgumentParser()
PARSER.add_argument('raw_config', help="A stringification of the run configuration. "
                                       "For example: {'run_env': 'DEV', 'server_secret_key': 'ServerKeyexport !', "
                                       "'sql_alchemy': {'create_tables': True, 'database_uri': 'sqlite:///:memory:', "
                                       "'track_modifications': False}, 'elasticsearch': "
                                       "{'dry_run': True, 'host': 'http://wp-p1m-50.ebi.ac.uk:9200'}, "
                                       "'admin_username': 'admin', 'admin_password': '123456', "
                                       "base_path': '/chembl/interface_api/delayed_jobs'}")
ARGS = PARSER.parse_args()

template = open('kubernetes_configmap_template.txt', 'r').read()
configmap = template.format(DELAYED_JOBS_RAW_CONFIG=ARGS.raw_config)
print(configmap)