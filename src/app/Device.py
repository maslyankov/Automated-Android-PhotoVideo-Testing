import os
import xml.etree.cElementTree as ET

import src.constants as constants


class Device():
    def __init__(self, serial, logs_enabled: bool = False, logs_filter: str = ''):
        print("Attaching to device...")
        device_serial = serial
        self.logs_enabled = logs_enabled
        self.logs_filter = logs_filter

        self.device_xml = os.path.join(constants.DEVICES_SETTINGS_DIR, f'{device_serial}.xml')

    def load_settings_file(self):
        print(f'Checking for Device settings file at "{self.device_xml}" and possibly loading it..')

        try:
            tree = ET.parse(self.device_xml)
        except FileNotFoundError:
            print("Settings file for device nonexistent! Clean slate... :)")
            return
        except ET.ParseError:
            print("Failed to load Device settings! :( XML Error!")
            return

        return tree.getroot()

    def set_logs(self, logs_bool, fltr=None):
        if not isinstance(logs_bool, bool):
            print('Logs setter got a non bool type... Defaulting to False.')
            self.logs_enabled = False
        else:
            self.logs_enabled = logs_bool

        if fltr is not None:
            self.logs_filter = fltr