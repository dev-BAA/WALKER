import os, platform
import json
import logging
import random
import re

import urllib
import urllib.request
import socket
import urllib.error

import requests
import imghdr
import datetime

#from scripts.common_functions import *


SCREENSHOTS_DIR = './screenshots/ BLOB/'
URL = 'blob:https://sushiwok.ru/78b72729-144a-4d15-b283-865cdfd950c7'
#save_screenshots(SCREENSHOTS_DIR, "01.xml", " YANDEX_XML_URL ", driver)
#driver.save_screenshot(SCREENSHOTS_DIR + "BLOB" + ".png")

#save_png(SCREENSHOTS_DIR, "777", URL)

file = SCREENSHOTS_DIR + "777" + ".png"
urllib.request.urlretrieve(URL, file)