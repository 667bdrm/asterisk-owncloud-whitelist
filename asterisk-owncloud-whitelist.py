#!/usr/bin/python
# -*- coding: utf-8 -*-

"""

  Asterisk Owncloud White+Black list AGI script
  Reads remote Owncloud contacts using CardDAV, rejecting incoming call if the caller id not in the contacts or marked as bad (has "Blocked" in the VCard Categories list)

  Copyright (C) 2017, 667bdrm

  This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
  
  
  Usage:
  
  1. Make file executable, put the file into agi-bin Asterisk directory
  2. Add the new extension to extensions.conf
  exten => 1234,1,AGI(asterisk-owncloud-whitelist.py,"owncloud.example.com","/remote.php/carddav/addressbooks/myusername/default","myusername","mypass","blacklist_sounds_subdirectory","blacklist_category")
  3. Restart Asterisk
  
"""
import sys
import re
import time
import random
import lxml.etree
import vobject
import requests
import datetime
import os
import fnmatch
import random

env = {}
tests = 0

def recursive_glob(treeroot, pattern):
    results = []
    for base, dirs, files in os.walk(treeroot):
        goodfiles = fnmatch.filter(files, pattern)
        results.extend(os.path.join(base, f) for f in goodfiles)
    return results

while 1:
   line = sys.stdin.readline().strip()

   if line == '':
      break
   key,data = line.split(':')
   if key[:4] <> 'agi_':
      #skip input that doesn't begin with agi_
      sys.stderr.write("Did not work!\n");
      sys.stderr.flush()
      continue
   key = key.strip()
   data = data.strip()
   if key <> '':
      env[key] = data

sys.stderr.write("AGI Environment Dump:\n");
sys.stderr.flush()
for key in env.keys():
   sys.stderr.write(" -- %s = %s\n" % (key, env[key]))
   sys.stderr.flush()

f = open(os.environ.get('AST_LOG_DIR', '') + '/agi_owncloud_whitelist.log', 'a+')



host = ""
path = ""
user = ""
password = ""
blacklist_sounds_path = ""
blacklist_category = "Blocked"

if len(sys.argv) >= 5:
    host = sys.argv[1]
    path = sys.argv[2]
    user = sys.argv[3]
    password = sys.argv[4]
    blacklist_sounds_path = sys.argv[5]
    blacklist_category = sys.argv[6]

    
f.write("\nIncoming call\nData source: %s\n" % host)
f.write(datetime.datetime.now().strftime("%Y-%m-%d %H:%M") + "\n")

for k in env.keys():
    if k.find('agi_arg_') == -1:
        f.write(k + ' = ' + env[k] + "\n")

black_found = False


headers = {'Content-Type': 'text/xml', 'Depth':'1'}
xml_data = "<card:addressbook-query xmlns:d='DAV:' xmlns:card='urn:ietf:params:xml:ns:carddav'><d:prop><d:getetag /><card:address-data /></d:prop></card:addressbook-query>"

sounds_path = os.environ.get('AST_VAR_DIR', '') + '/sounds/' +  env.get('agi_language', '')

blacklist_sounds = recursive_glob(sounds_path + '/' + blacklist_sounds_path, '*.gsm')

random_max = 0

if len(blacklist_sounds) > 1:
    random_max = len(blacklist_sounds) - 1

    blacklist_sound_index = random.randint(0, random_max)
    blacklist_sound = blacklist_sounds[blacklist_sound_index].replace(sounds_path + '/', '').replace('.gsm', '')
    
f.write("Requesting contacts\n")


request_url = 'https://' + host + path

try:

    response = requests.request('REPORT', request_url, data=xml_data, headers=headers, auth=(user, password))
except Exception as ex:
    f.write("Error requesting contacts")
    f.write(str(ex))



try:
    data = lxml.etree.fromstring(response.text.encode('utf-8', 'ignore'))
except Exception as ex:
    f.write("Error loading contacts\n")
    f.write(str(ex))
    
f.write("Loading contacts\n")

contacts = []

try:

    contacts =  data.xpath('//*/card:address-data', namespaces = {"d":"DAV:", "card":"urn:ietf:params:xml:ns:carddav"})
except:
    f.write('Cannot load contacts')

contact_found = False

black_found = False

for contact_elem in contacts:
    
    vcard = vobject.readOne(contact_elem.text)
    
    try:
        name = vcard.contents.get('fn',[])[0].value.encode('utf-8')
    except Exception as ex:
        f.write("Failed to get contact name\n")
        f.write(str(ex))
    
    for tel in vcard.contents.get('tel', []):
        raw_phone = tel.value
        
        phone = raw_phone.replace("+", "").replace(" ", "").replace("-", "")

        pattern = re.compile("^" + phone + '$')
        
        # if metch tel:
        if pattern.search(env.get('agi_callerid')):
            contact_found = True
            f.write("Found contact for %s\n" % phone)

            try:
                f.write("Contact: %s\n" % name)
           
              
                cats_data =  vcard.contents.get('categories', [])
    
                cats = []
    
                if len(cats_data) > 0:
                    cats = cats_data[0].value
        
                for cat in cats:
        
                    if cat == blacklist_category:
                        f.write("Blacklist found: %s %s\n" % (name, phone))
                        f.write("Selected sound = " + blacklist_sound + "\n")
                        black_found = True
        
            except Exception as ex:
                f.write("Failed to get contact categories\n")
                f.write(str(ex))
            
        
if len(contacts) == 0:
    print "NOOP\n"
elif contact_found == True and black_found == True:
    print "ANSWER\n"
    #print "EXEC PLAYBACK \"followme/sorry\"\n"
    #print "EXEC WAIT \"3\"\n"
    #print "EXEC PLAYBACK \"polkovnik/krasnogorsyi otdel\"\n"
    #print "EXEC WAIT \"3\"\n"
    #print "EXEC PLAYBACK \"polkovnik/vo mojete voenn yazokom\"\n"
    #print "EXEC WAIT \"2\"\n"
    #print "EXEC PLAYBACK \"polkovnik/ya polkovnik\"\n"
    print "EXEC WAIT \"4\"\n"
    print "EXEC PLAYBACK \"" + blacklist_sound + "\"\n"
    print "EXEC WAIT \"10\"\n"
    print "HANGUP\n"
elif contact_found == False:
    print "ANSWER\n"
    print "EXEC PLAYBACK \"followme/sorry\"\n"
    #print "EXEC PLAYBACK \"" + blacklist_sound + "\"\n"
    print "HANGUP\n"
    f.write("Contact not found: %s\n" % env.get('agi_callerid'))

f.close()

