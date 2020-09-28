import os
import time
import threading
import xml.etree.cElementTree as ET

from PySimpleGUI import cprint as gui_print
import src.constants as constants
from src.app.LightsCtrl import LightsCtrl
from src.konica.ChromaMeterKonica import ChromaMeterKonica


def dict_len(dict):
    res = 0
    for item in dict.keys():
        res += len(dict[item])
    return res


class AutomatedCase:
    def __new__(cls, *args, **kwargs):
        if args[2] == '':
            print("AutomatedCases received an empty lights xml...")
            raise Exception(ValueError)
        return super(AutomatedCase, cls).__new__(cls)

    def __init__(self, attached_devices, devices_obj,
                 lights_model, lights_seq_xml, luxmeter_model,
                 gui_window, gui_output,
                 specific_device=None):
        self.attached_devices = attached_devices
        self.devices_obj = devices_obj
        self.lights_model = lights_model
        self.lights_seq_xml = os.path.join(constants.ROOT_DIR, 'lights_seq', f'{lights_seq_xml}.xml')
        self.luxmeter_model = luxmeter_model
        self.specific_device = specific_device

        self.lights_seq = {}
        self.lights_seq_name = None
        self.lights_seq_desc = None

        self.gui_window = gui_window
        self.gui_output = gui_output

        self.parse_lights_xml_seq()

    def parse_lights_xml_seq(self):
        try:
            tree = ET.parse(self.lights_seq_xml)
        except FileNotFoundError:
            print("Lights sequence file nonexistent!")
            return
        except ET.ParseError:
            print("Failed to load Lights sequence file! :( XML Error!")
            return

        root = tree.getroot()
        counter = 0
        for elem in root:
            for subelem in elem:
                if subelem.tag == 'sequence':
                    # Each color temp
                    self.lights_seq[subelem.attrib["color_temp"]] = []
                    for data in subelem:
                        # Each LUX value
                        self.lights_seq[subelem.attrib["color_temp"]].append(int(data.text.strip()))

                    counter += 1
                elif subelem.tag == 'name':
                    self.lights_seq_name = subelem.text
                elif subelem.tag == 'description':
                    self.lights_seq_desc = subelem.text
                else:
                    print(f"{subelem.tag}: ", subelem.text)

    def output_gui(self, text, msg_type=None):
        if msg_type == 'error':
            text_color = 'white on red'
        else:
            text_color = None

        gui_print(text, window=self.gui_window, key=self.gui_output, colors=text_color)

    def _execute(self, gui_event):
        progress = 0
        progress_step = 100 / dict_len(self.lights_seq)

        if self.luxmeter_model == 'Konita Minolta CL-200A':  # Konita Minolta CL-200A Selected
            self.output_gui("Initializing Luxmeter...")
            luxmeter = ChromaMeterKonica()
        else:
            self.output_gui("Unsupported luxmeter selected!", msg_type='error')
            return

        self.output_gui('Initializing lights...')
        lights = LightsCtrl(self.lights_model)  # Create lights object
        if self.lights_model == 'SpectriWave':  # SpectriWave Specific
            time.sleep(1)
            lights_status = lights.status()
            self.output_gui(f"Lights Status: \n{lights_status}\n")

        for temp in list(self.lights_seq.keys()):
            self.output_gui(f'\nStarting Color Temp: {temp}')
            lights.set_brightness(1)
            lights.turn_on(temp)

            for lux in self.lights_seq[temp]:
                self.output_gui(f'Doing {lux} lux...')
                lights.set_lux(luxmeter, lux)

                # Do the thing
                if self.specific_device is None:
                    for device in self.attached_devices:
                        self.output_gui(f'Now executing using device {device} ({self.devices_obj[device].friendly_name})')
                        self.devices_obj[device].take_photo()
                else:
                    self.output_gui(f'Now executing using device {device} ({self.devices_obj[device].friendly_name})')
                    self.devices_obj[self.specific_device].take_photo()

                progress += progress_step
                # send progress to gui thread
                self.gui_window.write_event_value(
                    gui_event,
                    progress
                )

            self.output_gui(f'{temp} is done! Turning it off.')
            lights.turn_off(temp)

        lights.disconnect()

    def execute(self, gui_event):
        threading.Thread(target=self._execute, args=(gui_event,), daemon=True).start()

