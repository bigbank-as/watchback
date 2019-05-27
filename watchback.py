#!/usr/bin/python3

import os
import csv
import sys
import json
import textwrap
from elasticsearch import Elasticsearch
from ssl import create_default_context
from lib.watcherimporter import WatcherImporter
import logging
from getpass import getpass

config_loc = os.environ["HOME"] + "/.watchback-config"
log_level = "standard"
password = ""

def _result_out(res, loc):
	files = os .listdir(loc)
	files_nr = len(files)

	print()
	print("     Watchback Results")
	print("─" * 27)
	print(" Total watchers: {:>9}".format(files_nr))
	print(" Uploaded watchers: {:>6}".format(res))
	print(" Failed watchers: {:>8}".format(files_nr - res))
	#print("Total watchers: %7s\n" \
	#	  "Uploaded watchers: %4s\n" \
	#	  "Failed watchers: %4s" % (str(files_nr), str(res), str(files_nr - res)))
	print("─" * 27)
	print()

def _logger_factory():
    global log_level

    logger = logging.getLogger()
    handler = logging.StreamHandler(sys.stdout)

    if log_level == "debug":
    	logger.setLevel(logging.INFO)
    	handler.setLevel(logging.INFO)
    else:
    	logger.setLevel(logging.ERROR)
    	handler.setLevel(logging.ERROR)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    return logger

def _setup_cli_args():
	global password, log_level
	args = {}

	while True:
		try:
			with open(config_loc) as json_file:
				args = json.load(json_file)
				break
		except:
			def_data = {"username": "jane.doe", \
						"watch-dir": "/dir/to/watchers", \
						"cert": "/dir/to/certificate", \
						"host": "localhost", \
						"port": 3000, \
						"dry_run": False, \
						"insecure": False}

			with open(config_loc, "w") as outfile:
				json.dump(def_data, outfile)

	username = input("Username (default: %s): " % args["username"])
	if username != "":
		args["username"] = username

	password = getpass(prompt="Password: ")

	out_level = input("Output level standard/debug (default: standard): ")
	if out_level == "debug":
		log_level = "debug"
	else:
		log_level = "standard"

	watch_dir = input("Watcher directory (default: %s): " % args["watch-dir"])
	if watch_dir != "":
		args["watch-dir"] = watch_dir

	cert = input("Certificate (default: %s): " % args["cert"])
	if cert != "":
		args["cert"] = cert 

	host = input("Host (default: %s): " % args["host"])
	if host != "":
		args["host"] = host
	
	port = input("Port (default: %s): " % args["port"])
	if port != "":
		args["port"] = port

	dry_run = input("Dry-run (default: %s): " % args["dry_run"])
	if dry_run == "True":
		args["dry_run"] = True
	else:
		args["dry_run"] = False
					
	insecure = input("Insecure (default: %s): " % args["insecure"])
	if insecure == "True":
		args["insecure"] = True
	else:
		args["insecure"] = False
			
	with open(config_loc, "w") as outfile:
		json.dump(args, outfile)

	return args

def main():
    global password
    args = _setup_cli_args()
    logger = _logger_factory()

    if args["insecure"]:
        logger.critical('I\'m sorry Dave, I\'m afraid I can\'t do that. ' +
                        'I just prevented you from shooting your own foot with a ' +
                        '2-barrel shotgun, loaded with glass shrapnel from broken whiskey bottles.')
        logger.critical('Instead of disabling TLS certificate verification, look up the correct ' +
                        'CA to use and specify it.')
        sys.exit(1)

    auth = (args["username"], password) if args["username"] and password else None
    try:
        ssl_context = create_default_context(cafile=args["cert"])
    except FileNotFoundError:
        logger.fatal('Unable to find the CA file %s', args["cert"])
        sys.exit(1)

    elastic = Elasticsearch(
        args["host"],
        http_auth=auth,
        scheme='http' if args["insecure"] else 'https',
        port=args["port"],
        ssl_context=ssl_context,
    )

    logger.info('Starting to sync Watchers from local folder %s to remote Elasticsearch %s:%d', args["watch-dir"],
                args["host"], args["port"])

    importer = WatcherImporter(elastic, args["watch-dir"], logger)

    count = 0
    res = importer.run(count, args["dry_run"])
    _result_out(res, args["watch-dir"])

    logger.info('Finished importing Watchers')

if __name__ == '__main__':
    main()
