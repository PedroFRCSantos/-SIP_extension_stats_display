#!/usr/bin/env python

# Python 2/3 compatibility imports
from __future__ import print_function

# standard library imports
import json
import subprocess
import time

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
        u"/statset", u"plugins.stats_display.settings",
        u"/statjson", u"plugins.stats_display.settings_json",
        u"/statupdate", u"plugins.stats_display.update",
    ]
)
# fmt: on

# Add this plugin to the plugins menu
gv.plugin_menu.append([u"Statistics Display", u"/statset"])

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


class settings(ProtectedPage):
    """Load an html page for entering cli_control commands"""

    def GET(self):
        return template_render.stats_display(statsDisplayDef)


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
