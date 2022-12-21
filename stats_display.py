#!/usr/bin/env python

# Python 2/3 compatibility imports
from __future__ import print_function

# standard library imports
import json
import subprocess
import time
import datetime

# local module imports
from blinker import signal
import gv  # Get access to SIP's settings, gv = global variables
from sip import template_render
from urls import urls  # Get access to SIP's URLs
import web
from webpages import ProtectedPage

# Add a new url to open the data entry page.
# fmt: off
urls.extend(
    [
        u"/stathome", u"plugins.stats_display.home",
        u"/statstartsip", u"plugins.stats_display.turn_on_sip",
        u"/statjson", u"plugins.stats_display.settings_json",
        u"/statupdate", u"plugins.stats_display.update",
        u"/statrawval", u"plugins.stats_display.raw_valves_stats",
        u"/statrawvalday", u"plugins.stats_display.raw_valves_stats_by_day",
    ]
)
# fmt: on

# Add this plugin to the plugins menu
gv.plugin_menu.append([u"Statistics Display", u"/stathome"])

statsDisplayDef = {}

# Read in the commands for this plugin from it's JSON file
def load_commands():
    global statsDisplayDef

    try:
        with open(u"./data/stats_display.json", u"r") as f:
            statsDisplayDef = json.load(f)  # Read the commands from file
    except IOError:  #  If file does not exist create file with defaults.
        statsDisplayDef = {}
        with open(u"./data/stats_display.json", u"w") as f:
            json.dump(statsDisplayDef, f, indent=4)
    return


load_commands()

#### output command when signal received ####
def on_zone_change(name, **kw):
    pass


zones = signal(u"zone_change")
zones.connect(on_zone_change)

################################################################################
# Web pages:                                                                   #
################################################################################

class home(ProtectedPage):
    """Load an html page for entering cli_control commands"""

    def GET(self):
        return template_render.stats_display_home()

def check_if_db_logger_active():
    # Check if DB logger is active
    global gv
    dbLogActive = False
    for testName in gv.plugin_menu:
        if testName[1] == "/dblog":
            dbLogActive = True

    return dbLogActive

class raw_valves_stats(ProtectedPage):
    """Load an html page for entering cli_control commands"""

    def GET(self):
        rawValvesData = []
        listOfValves = []

        qdict = web.input()

        dbLogActive = check_if_db_logger_active()

        if dbLogActive:
            from db_logger_valves import get_list_of_valves, estimate_valve_turnon_by_month, estimte_time_str_2_hour_float

            listOfValves = get_list_of_valves()

            rawValveId = 0
            qdict = web.input()
            if u"valveId" in qdict:
                try:
                    rawValveId = int(qdict[u"valveId"])
                    if rawValveId < 0:
                        rawValveId = 0
                except ValueError:
                    pass

            minYear = datetime.datetime.now().year - 1
            minMonth = datetime.datetime.now().month + 1
            if minMonth > 12:
                minMonth  = 1
                minYear = minYear + 1

            maxYear = datetime.datetime.now().year
            maxMonth = datetime.datetime.now().month

            if u"yearMin" in qdict:
                try:
                    minYear = int(qdict[u"yearMin"])
                    if minYear < 0:
                        minYear = 0
                except ValueError:
                    pass

            if u"monthMin" in qdict:
                try:
                    minMonth = int(qdict[u"monthMin"])
                    if minMonth < 0:
                        minMonth = 0
                except ValueError:
                    pass

            if u"yearMax" in qdict:
                try:
                    maxYear = int(qdict[u"yearMax"])
                    if maxYear < 0:
                        maxYear = 0
                except ValueError:
                    pass

            if u"monthMax" in qdict:
                try:
                    maxMonth = int(qdict[u"monthMax"])
                    if maxMonth < 0:
                        maxMonth = 0
                except ValueError:
                    pass

            if minYear > maxYear or (minYear == maxYear and minMonth > maxMonth):
                minYear = maxYear
                minMonth = maxMonth

            rawValvesData = estimate_valve_turnon_by_month(rawValveId, minYear, minMonth, maxYear, maxMonth)

        stringX = ""
        for key in rawValvesData:
            stringX = stringX +" "+ str(key.replace('-', '')) +","

        stringY = ""
        for key in rawValvesData:
            stringY = stringY +", "+ str(estimte_time_str_2_hour_float(rawValvesData[key]))
        stringY = stringY[2:]

        return template_render.stats_display_raw_valves_by_months(rawValvesData, listOfValves, rawValveId, minYear, minMonth, maxYear, maxMonth, datetime.datetime.now().year, datetime.datetime.now().month, stringX, stringY)

class raw_valves_stats_by_day(ProtectedPage):
    """Load an html page for entering cli_control commands"""

    def GET(self):
        rawValvesData = []
        listOfValves = []

        qdict = web.input()

        dbLogActive = check_if_db_logger_active()

        if dbLogActive:
            from db_logger_valves import get_list_of_valves, estimate_valve_turnon_by_day, estimte_time_str_2_hour_float

            listOfValves = get_list_of_valves()

            rawValveId = 0
            qdict = web.input()
            if u"valveId" in qdict:
                try:
                    rawValveId = int(qdict[u"valveId"])
                    if rawValveId < 0:
                        rawValveId = 0
                except ValueError:
                    pass

            minYear = datetime.datetime.now().year
            minMonth = datetime.datetime.now().month
            minDay = 1

            if u"dateMin" in qdict:
                try:
                    dateMinSplit = qdict[u"dateMin"].split('-')
                    if len(dateMinSplit) == 3:
                        minYear = int(dateMinSplit[0])
                        minMonth = int(dateMinSplit[1])
                        minDay = int(dateMinSplit[2])
                except ValueError:
                    pass

            maxYear = datetime.datetime.now().year
            maxMonth = datetime.datetime.now().month
            maxDay = datetime.datetime.now().day

            if u"dateMax" in qdict:
                try:
                    dateMinSplit = qdict[u"dateMax"].split('-')
                    if len(dateMinSplit) == 3:
                        maxYear = int(dateMinSplit[0])
                        maxMonth = int(dateMinSplit[1])
                        maxDay = int(dateMinSplit[2])
                except ValueError:
                    pass

            rawValvesData = estimate_valve_turnon_by_day(rawValveId, minYear, minMonth, minDay, maxYear, maxMonth, maxDay)

            stringX = ""
            for key in rawValvesData:
                stringX = stringX +" "+ str(key.replace('-', '')) +","

            stringY = ""
            for key in rawValvesData:
                stringY = stringY +", "+ str(estimte_time_str_2_hour_float(rawValvesData[key]))
            stringY = stringY[2:]

        return template_render.stats_display_raw_valves_by_day(rawValvesData, listOfValves, rawValveId, minYear, minMonth, minDay, maxYear, maxMonth, maxDay, datetime.datetime.now().year, datetime.datetime.now().month, datetime.datetime.now().day, stringX, stringY)

class turn_on_sip(ProtectedPage):
    """Load an html page for entering cli_control commands"""

    def GET(self):
        # Check if DB logger is active
        dbLogActive = check_if_db_logger_active()

        if dbLogActive:
            from db_logger_SIP_start import estimate_number_of_turn_on_by_month

            turnOnByMothStats = estimate_number_of_turn_on_by_month()
        else:
            turnOnByMothStats = {}

        stringX = ""
        for key in turnOnByMothStats:
            stringX = stringX +" "+ str(key.replace('-', '')) +","

        stringY = ""
        for key in turnOnByMothStats:
            stringY = stringY +", "+ str(turnOnByMothStats[key])
        stringY = stringY[2:]

        return template_render.stats_display_turn_on_sip(turnOnByMothStats, stringX, stringY)


class settings_json(ProtectedPage):
    """Returns plugin settings in JSON format"""

    def GET(self):
        web.header(u"Access-Control-Allow-Origin", u"*")
        web.header(u"Content-Type", u"application/json")
        return json.dumps(statsDisplayDef)

class update(ProtectedPage):
    """Save user input to cli_control.json file"""

    def GET(self):
        global statsDisplayDef
        qdict = web.input()

        with open(u"./data/stats_display.json", u"w") as f:  # write the settings to file
            json.dump(statsDisplayDef, f, indent=4)
        raise web.seeother(u"/restart")
