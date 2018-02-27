import requests
import json
import time
import csv
from collections import Counter
import configparser

Config = configparser.ConfigParser()

Config.read("dsl.properties")


print ("the sections are")
print (Config.sections())


def ConfigSectionMap(section):
    dict1 = {}
    options = Config.options(section)
    for option in options:
        try:
            dict1[option] = Config.get(section, option)
            if dict1[option] == -1:
                print ("skip: %s" % option)
        except:
            print("exception on %s!" % option)
            dict1[option] = None
    return dict1


dimensionsUserName = ConfigSectionMap("Dimensions")['dimensionsusername']
dimensionsPassword = ConfigSectionMap("Dimensions")['dimensionspassword']



auth_data = {
  'username': dimensionsUserName,
  'password': dimensionsPassword
}

url = 'https://dsl.dimensions.ai'

global headers 

api_url = url + '/api'

def renewtoken():
    global headers
    auth_result = requests.post(url + '/login', json=auth_data)
    access_token = auth_result.json()['token']
    headers = {
        'Authorization': 'JWT {}'.format(access_token)
    }
    return headers

renewtoken()

def dslquery(data, retries=0):
    #print (retries)
    jsonresult={}
    result = requests.post(api_url, headers=headers,data=data)
    try:
        jsonresult =json.loads(result.text)
    except:
        print (headers)
        print ("a json object was not produced...sleeping for 30 seconds")
        print (data)
        print (result.text)
        time.sleep(2)
        if retries < 1:
            retries = retries + 1
            renewtoken()
            jsonresult = dslquery(data, retries)
        else:
            jsonresult = {"error":result.text}
            print (jsonresult)
            
    return jsonresult




