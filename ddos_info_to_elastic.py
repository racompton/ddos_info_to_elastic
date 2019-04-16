#!/usr/bin/python3

import requests
import json
import urllib3
import datetime
import argparse
import sys
import logging
import logging.handlers
import platform
import time
import operator
from elasticsearch import Elasticsearch
import copy

if sys.version_info<(3,0,0):
   sys.stderr.write("You need python 3.0+ or later to run this script\n")
   exit(1)


parser = argparse.ArgumentParser(description='This script retrieves the list of DDoS attacks that occured the last X number of minutes and puts it in elasticsearch.')
parser.add_argument('-k','--key', help='Specify an API key',required=True)
parser.add_argument('-u','--user',help='Specify a username', required=True)
parser.add_argument('-m','--minutes',help='Specify the number of minutes of historical info to retrieve', required=True)
parser.add_argument('-l','--limit',help='Specify the number of events to limit the results to (default is unlimited)', required=False, default=0)
parser.add_argument('--debug', action='store_true', help='Enable debug mode',required=False)
args = parser.parse_args()


# set the value of these strings from the command line arguments
api_key = args.key
username = args.user
minutes = args.minutes
limit = args.limit
debug = args.debug

# Try to convert minutes to a string and error out if I can't
try:
    minutes = int(minutes)
except ValueError:
    print ("Doesn't look like minutes (-m or --minutes) is an integer")
    sys.exit(1)

# Get time from X mins ago
minsago = datetime.datetime.utcnow() - datetime.timedelta(minutes=minutes)

# Convert time to formated timestamp
timestamp = str(minsago.year)+"-"+str('{:02d}'.format(minsago.month))+"-"+str('{:02d}'.format(minsago.day))+"T"+str('{:02d}'.format(minsago.hour))+":"+str('{:02d}'.format(minsago.minute))+":"+str('{:02d}'.format(minsago.second))+".0Z"

if debug:
    print("The timestamp variable is set to: "+timestamp)

# Disable the SSL Cert warnings on a self signed cert (Not recommended!)
#urllib3.disable_warnings()

# Set up the payload
payload = {'username': username, 'api_key': api_key, 'modifiedSince': timestamp, 'limit': limit, 'sortBy':'numberOfTimesSeen'}

if debug:
    print("The username variable has been set to: "+username)
    print("The api_key variable has been set to: "+api_key)
    print("The limit variable has been set to: "+limit)

try:
# Make the API get request
# Add verify=False at the end if there is a self signed cert (not recommended!)
    response = requests.get('https://dis-demo2.cablelabs.com/api/v1/data_distribution_resource/', params=payload, verify=False)
#    response = requests.get('https://dis-demo2.cablelabs.com/api/v1/data_distribution_resource/', params=payload)

except requests.exceptions.HTTPError as e:
    if debug:
        print("Uh oh we got an http error! ")
    print (e)
    sys.exit(1)
except requests.exceptions as e:
    if debug:
        print("Uh oh we got a requests error! ")
    print (e)
    sys.exit(1)

if debug:
    print ("The server returned: "+str(response.content))

try:
# Put the json results into a dictionary
    data = response.json()
    if debug:
        print("The data dictionary is set to: "+ str(data))
except Exception as e :
    print("We got an error trying to put the returned data into a dictionary")
    print (e)
    sys.exit(1)

es = Elasticsearch([{'host': 'localhost', 'port': 9200}])

def elk_write(es, incident):
    #insert
    es.index(index="dis_info", doc_type="json", body=incident)

# Is the don't delete arg set?
if debug:
    print("I am now putting the events that were pulled down into the Elasticsearch database")

for IPaddress in data.get('outputData'):
    serialized_IPaddress = copy.deepcopy(IPaddress)
    del serialized_IPaddress['events']
# Combine the Longitude and Latitude so that Kibana will do map visualizations on the location field    
    serialized_IPaddress['location'] = "{},{}".format(serialized_IPaddress['Latitude'],serialized_IPaddress['Longitude'])
    for event in IPaddress.get('events'):
        serialized_IPaddress['event'] = event
        elk_write(es, serialized_IPaddress)
