# Uses https://github.com/Swind/pure-python-adb
import subprocess
import os
from ppadb.client import Client as AdbPy
import src.constants as constants

class AutomatedCase():
    def __init__(self):
