import subprocess
import time
import re
import os
import xml.etree.cElementTree as ET
from natsort import natsorted

from src.app.Device import Device
from src.utils.xml_tools import generate_sequence, xml_from_sequence

import src.constants as constants


class USBCamDevice(Device):
    def __init__(self, serial, port):
        super().__init__(serial)

        self.port = port

