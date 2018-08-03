#!/usr/bin/env python3

import os
import sys
import argparse
from elasticsearch import Elasticsearch
from ssl import create_default_context
from lib.watcherimporter import WatcherImporter
import logging
from argparse import RawDescriptionHelpFormatter


def _logger_factory():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    return logger


def _setup_cli_args():
    parser = argparse.ArgumentParser(formatter_class=RawDescriptionHelpFormatter, description=r"""
Sync Elasticsearch Watchers from local JSON files to remote Elasticsearch

This program takes a directory of Elasticsearch Watchers (as JSON files)
and syncs them to a remote Elasticsearch.

Usage Example:

./watchback.py --es-ca Corporate_Root_CA.crt \
    --es-user=bruce.wayne \
    --es-pass=YouNeverSeeMeComing \
    --es-host=elasticsearch.localhost \
    --es-port=9200 \
    --watcher-dir=/home/bruce/vigilante/watchlist

""")
    parser.add_argument('--watcher-dir', metavar='dirpath', nargs='+', default='watchers',
                        help='Directory containing watch definitions')
    parser.add_argument('--dry-run', default=False, action='store_true',
                        help='run validation checks, but do not actually modify anything on the remote API')
    parser.add_argument('--es-ca', metavar='ca', default=None,
                        help='A X509 trusted CA file to use for Elasticsearch HTTPS connections')
    parser.add_argument('--es-host', metavar='host', required=True, action='append',
                        help='Elasticsearch API hostname(s)')
    parser.add_argument('--es-user', metavar='user', help='Username for Elasticsearch authentication', nargs='?',
                        default=None)
    parser.add_argument('--es-pass', metavar='pass', help='Password for Elasticsearch authentication', nargs='?',
                        default=None)
    parser.add_argument('--es-insecure',
                        help='''
                        Use unencrypted HTTP to connect to Elasticsearch.
                        HTTPS is used when this argument is not specified.
                        ''',
                        action='store_true',
                        default=False)
    parser.add_argument('--es-port', metavar='port', type=int, help='Port of Elasticsearch API', nargs='?',
                        default=9200)
    return parser.parse_args()


def main():
    args = _setup_cli_args()
    logger = _logger_factory()

    if args.es_insecure:
        logger.critical('I\'m sorry Dave, I\'m afraid I can\'t do that. ' +
                        'I just prevented you from shooting your own foot with a ' +
                        '2-barrel shotgun, loaded with glass shrapnel from broken whiskey bottles.')
        logger.critical('Instead of disabling TLS certificate verification (--es-insecure), look up the correct ' +
                        'CA to use and specify it using --es-ca.')
        sys.exit(1)

    watcher_dir = os.path.abspath(args.watcher_dir)
    auth = (args.es_user, args.es_pass) if args.es_user and args.es_pass else None
    try:
        ssl_context = create_default_context(cafile=args.es_ca)
    except FileNotFoundError:
        logger.fatal('Unable to find the CA file %s', args.es_ca)
        sys.exit(1)

    elastic = Elasticsearch(
        args.es_host,
        http_auth=auth,
        scheme='http' if args.es_insecure else 'https',
        port=args.es_port,
        ssl_context=ssl_context,
    )

    logger.info('Starting to sync Watchers from local folder %s to remote Elasticsearch %s:%d', watcher_dir,
                args.es_host, args.es_port)

    importer = WatcherImporter(elastic, args.watcher_dir, logger)

    try:
        importer.selftest()
    except Exception as e:
        logger.fatal('Unable to connect to Elasticsearch.')
        logger.fatal(str(e))
        sys.exit(1)

    importer.run(args.dry_run)
    logger.info('Finished importing Watchers')


if __name__ == '__main__':
    main()
