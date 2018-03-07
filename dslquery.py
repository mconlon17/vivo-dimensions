#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    dslquery.py: Simple query of Dimensions

"""

import requests
import json
import time
import configparser
import sys

config = configparser.ConfigParser()
config.read("dsl.properties")
url = 'https://dsl.dimensions.ai'
api_url = url + '/api'


def config_section(section):
    dict1 = {}
    options = config.options(section)
    for option in options:
        try:
            dict1[option] = config.get(section, option)
            if dict1[option] == -1:
                print ("skip: %s" % option)
        except ValueError:
            print("exception on %s!" % option)
            dict1[option] = None
    auth_dat = dict()
    auth_dat['username'] = dict1['dimensionsusername']
    auth_dat['password'] = dict1['dimensionspassword']
    return auth_dat

auth_data = config_section("Dimensions")


def renew_token():
    try:
        auth_result = requests.post(url + '/login', json=auth_data)
        access_token = auth_result.json()['token']
    except ValueError:
        print "Unable to authenticate to Dimensions API"
        sys.exit(1)
    header = {
        'Authorization': 'JWT {}'.format(access_token)
    }
    return header

headers = renew_token()


def dslquery(data, retries=0):
    result = {}
    try:
        result = requests.post(api_url, headers=headers, data=data)
        json_result = json.loads(result.text)
    except IOError:
        print headers
        print "a json object was not produced...sleeping for 2 seconds"
        print data
        print retries
        print result.text
        time.sleep(2)
        if retries > 0:
            retries -= 1
            renew_token()
            json_result = dslquery(data, retries)
        else:
            print "Retries exceeded"
            json_result = {"error": result.text}
            print json_result
            
    return json_result
