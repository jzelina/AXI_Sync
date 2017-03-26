#!/usr/bin/python

# requirements
import socket
import logging
import datetime
import xml.dom.minidom
from ConfigParser import SafeConfigParser
import os
import ssl
import time
import xml.etree.ElementTree as ET

"""
Title: AXI_Sync
----------------------
Script to connect with SIP-DECT system(s) via AXI
and perform, configuration, update or inventory operations.

About:
------
This tool connects via AXI to a given list of SIP-DECT systems (OMMs).
Depending on the configured mode the following actions can be performed:

- inventory: log some system information (good to test script as no changes are performed)
- operation: (none, setconfig, update)
# none = no operation, good for test
# setconfig = Set the ConfigURL + Credentials if provided
# update = Initiate a software and configuration update request. (Update Button)
"""
__author__ = "Julian Zelina"
__version__ = "0.1"
__name__ = "AXI_Sync"

# enable debug
debug = True

myfolder = os.path.dirname(os.path.realpath(__file__))

# logging
today = datetime.date.today()
logger = logging.getLogger("AXI-Sync")
logger.setLevel(logging.INFO)

# create a file handler
handler = logging.FileHandler(myfolder + '/logs/' + str(today) + '.log')
handler.setLevel(logging.INFO)

# create a logging format
formatter = logging.Formatter('%(asctime)s - %(message)s')
handler.setFormatter(formatter)

# add the handlers to the logger
logger.addHandler(handler)


############################
# function

def echo_debug(text, isdebug):
    logger.info(text)

    if isdebug:
        print(text)


def get_updatemin():
    tmp_count = 0
    tmp_minute = {}

    for index in range(0, 60):
        tmp_minute[tmp_count] = index
        tmp_count += 1
    return tmp_minute


def get_response(self):
    # echo_debug("AXI.recv", debug)
    mybuffer = b''
    while b'\x00' not in mybuffer:
        r = self.recv(4096)
        if not r:
            break
        mybuffer += r
    pos = mybuffer.find(b'\x00')
    if pos >= 0:
        last_response = mybuffer[:pos]
        mybuffer = mybuffer[pos + 1:]

        # echo_debug(("<< ", last_response), debug)
        return xml.dom.minidom.parseString(last_response)
    return None


############################
echo_debug("\n\nSTART {0}".format(str(__name__) + " - " + str(__version__)), debug)

# import configuration
echo_debug("Import configuration", debug)
config = SafeConfigParser()
config.read(myfolder + '/config/config.cfg')

# config file values
debug = bool(config.get('config', 'debug'))
username = str(config.get('config', 'username'))
password = str(config.get('config', 'password'))
inventory = bool(config.get('config', 'inventory'))
mode = str(config.get('config', 'mode'))
systemscfg = str(config.get('config', 'systems'))
stream = "ssl"  # Use "tcp" or "ssl" connection to OMM.
ConfigURL = str(config.get('config', 'ConfigURL'))
Credentials = str(config.get('config', 'Credentials'))
UpdateHour = str(config.get('config', 'UpdateHour'))
delay = int(config.get('config', 'delay'))

echo_debug("Inventory: " + str(inventory), debug)

# start script

# check if mode is valid
if mode == "none" or mode == "update" or mode == "setconfig":
    echo_debug("Mode: " + mode, debug)
else:
    echo_debug("Mode: " + mode, debug)
    echo_debug("No valid mode configured. (none,update,setconfig)", debug)
    quit()

# read list of systems
with open(myfolder + systemscfg) as f:
    lines = f.readlines()

echo_debug("Number of Lines: {0}".format(str(len(lines))), debug)

# read system list
# expected format:
# OMM-IP;

item = ""
systems = []
sysminute = {}
skipped = 0

if len(lines) > 0:
    for item in lines:
        # echo_debug("read line: " + item, debug)
        tmp_val = item.split(";")

        try:
            # TODO: validate if input is an IP-Address
            if tmp_val[0].count(".") == 3:
                echo_debug("-> Add system to list: " + tmp_val[0], debug)
                systems.append(tmp_val[0].rstrip())

                if isinstance(int(tmp_val[1]), (int, long)):
                    if int(tmp_val[1].rstrip()) < 60:
                        sysminute[tmp_val[0].rstrip()] = tmp_val[1].rstrip()
            else:
                skipped += 1
                echo_debug("-> Ignore this line.", debug)
        except:
            skipped += 1
            echo_debug("-> Ignore this line by except.", debug)
else:
    echo_debug("Systems list is empty!!. Exit script.", debug)
    quit()

# print systems
echo_debug("Number of SIP-DECT systems: {0}".format(str(len(systems))), debug)
echo_debug("Number of SIP-DECT minute timers: {0}".format(str(len(sysminute))), debug)
if len(systems) == 0:
    echo_debug("Systems list is empty!!. Exit script.", debug)
    quit()

# calculate update timer minute from range based on system size.
update_minute = get_updatemin()
update_count = 0

# connect to OMM
# for each OMM
for ommip in systems:

    try:
        echo_debug("--------------------------", debug)
        echo_debug("Connect to OMM: " + ommip, debug)

        if stream == "tcp":

            # Establish TCP connection
            echo_debug("Establish TCP! connection, non SSL!!", debug)
            s = socket.create_connection((ommip, 12621), 5)
            s.settimeout(5)

        else:

            # Establish secure SSL without validations.
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            s = ssl.wrap_socket(sock, keyfile=None, certfile=None, server_side=False)
            s.connect((ommip, 12622))

        # login
        MESSAGE = '<Open seq="150" protocolVersion="41" username="' + username + '" password="' + password + '" />\0'
        s.send(MESSAGE)
        data = get_response(s)
        root = ET.fromstring(data.toxml())
        echo_debug("OMM Version: " + root.attrib['ommVersion'], debug)

        # inventory
        if inventory is True:
            # inventory: PhoneState, Heath,
            # GetSystemName
            MESSAGE = '<GetSystemName />\0'
            s.send(MESSAGE)
            data = get_response(s)
            root = ET.fromstring(data.toxml())
            echo_debug("SysName: " + root.attrib['name'], debug)

            # GetSystemName
            MESSAGE = '<GetConfigURL />\0'
            s.send(MESSAGE)
            data = get_response(s)
            echo_debug("Current ConfigURL: " + data.toxml(), debug)

            # HealthState
            MESSAGE = '<GetHealthState />\0'
            s.send(MESSAGE)
            data = get_response(s)
            echo_debug("HealthState: " + data.toxml(), debug)

            # User Summary
            MESSAGE = '<GetPPUserSummary />\0'
            s.send(MESSAGE)
            data = get_response(s)
            echo_debug("GetPPUserSummary: " + data.toxml(), debug)

            # RFP Summary
            MESSAGE = '<GetRFPSummary />\0'
            s.send(MESSAGE)
            data = get_response(s)
            echo_debug("GetRFPSummary: " + data.toxml(), debug)

        # action
        # mode: none, setconfig, update
        if mode == "none":
            echo_debug("No mode defined, no action will be initiated.", debug)

        if mode == "update":
            # Trigger reload of configuration and software
            echo_debug("Send update request.", debug)
            MESSAGE = '<SoftwareUpdate />\0'
            s.send(MESSAGE)
            data = get_response(s)
            # print "received data:", data.toxml()

        if mode == "setconfig":
            echo_debug("Set the ConfigURL.", debug)

            if ConfigURL:
                MESSAGE = ConfigURL + '\0'
                s.send(MESSAGE)
                data = get_response(s)
                echo_debug("ConfigURL Response: " + data.toxml(), debug)

            if Credentials:
                MESSAGE = Credentials + '\0'
                s.send(MESSAGE)
                data = get_response(s)
                echo_debug("Credential Response: " + data.toxml(), debug)

            if UpdateHour:

                try:
                    if sysminute[ommip]:
                        echo_debug("Minute set for system in ip.csv: " + sysminute[ommip] + "\n", debug)
                        MESSAGE = '<SetSystemProvUpdTrig enable="1" hour="' + str(UpdateHour) + '" minute="' + str(
                            sysminute[ommip]) + '" />' + '\0'
                except:
                    MESSAGE = '<SetSystemProvUpdTrig enable="1" hour="' + str(UpdateHour) + '" minute="' + str(
                        update_minute[update_count]) + '" />' + '\0'
                s.send(MESSAGE)
                data = get_response(s)
                echo_debug("SetSystemProvUpdTrig Response: " + data.toxml(), debug)

        # close tcp connection
        echo_debug("close connection to " + ommip + "\n", debug)
        s.close()

        # sleep delay timer
        time.sleep(delay)

    except:
        echo_debug("ERROR could not connect to " + ommip, debug)

    # increase update timer count (0..59, than 0..59)
    update_count += 1
    if update_count >= 60:
        update_count = 0

        # end loop

# exit
