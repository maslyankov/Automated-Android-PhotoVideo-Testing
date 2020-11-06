import os

import src.constants as constants


class Device():
    def __init__(self, serial, logs_enabled: bool = False, logs_filter: str = ''):
        print("Attaching to device...")
        device_serial = serial
        self.logs_enabled = logs_enabled
        self.logs_filter = logs_filter

        self.device_xml = os.path.join(constants.DEVICES_SETTINGS_DIR, f'{device_serial}.xml')
