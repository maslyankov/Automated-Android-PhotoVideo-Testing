import os
import time
import threading
import xml.etree.cElementTree as ET
from pathlib import Path

from PySimpleGUI import cprint as gui_print
import src.constants as constants
from src.app.LightsCtrl import LightsCtrl
from src.konica.ChromaMeterKonica import ChromaMeterKonica


def dict_len(dictionary):
    res = 0
    for item in dictionary.keys():
        res += len(dictionary[item])
    return res


class AutomatedCase:
    def __new__(cls, *args, **kwargs):
        if args[2] == '':
            print("AutomatedCases received an empty lights xml...")
            raise Exception(ValueError)
        return super(AutomatedCase, cls).__new__(cls)

    def __init__(self, attached_devices, devices_obj,
                 lights_model, lights_seq_xml, luxmeter_model,
                 pull_files_bool, pull_files_location,
                 gui_window, gui_output, gui_event,
                 specific_device=None):
        self.attached_devices = attached_devices
        self.devices_obj = devices_obj

        self.lights_model = lights_model
        self.lights_seq_xml = os.path.join(constants.ROOT_DIR, 'lights_seq', f'{lights_seq_xml}.xml')
        self.luxmeter_model = luxmeter_model

        self.pull_files_bool = pull_files_bool
        self.pull_files_location = pull_files_location

        self.gui_window = gui_window
        self.gui_output = gui_output
        self.gui_event = gui_event

        self.specific_device = specific_device

        self.lights_seq = {}
        self.lights_seq_name = None
        self.lights_seq_desc = None

        self.stop_signal = False

        self.progress = 0

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
            self.gui_window.write_event_value(
                self.gui_event,
                {
                    'progress': self.progress,
                    'error': True
                }
            )
        else:
            text_color = None

        gui_print(text, window=self.gui_window, key=self.gui_output, colors=text_color)

    def pull_new_images(self, folder, filename):
        if self.specific_device is None:
            for device in self.attached_devices:
                dest = os.path.join(
                    os.path.normpath(self.pull_files_location),
                    self.devices_obj[device].friendly_name,
                    folder)
                Path(dest).mkdir(parents=True, exist_ok=True)

                print("current list of files: ", self.devices_obj[device].get_camera_files_list())
                self.output_gui(f'Now pulling from device {device} ({self.devices_obj[device].friendly_name})')
                self.devices_obj[device].pull_and_rename(
                    dest,
                    filename
                )
                self.devices_obj[device].clear_folder('sdcard/DCIM/Camera/')
        else:
            self.output_gui(
                f'Now pulling from {self.specific_device} ({self.devices_obj[self.specific_device].friendly_name})'
            )
            self.devices_obj[self.specific_device].pull_and_rename(
                os.path.join(
                    os.path.normpath(self.pull_files_location),
                    self.devices_obj[self.specific_device].friendly_name,
                    folder
                ),
                filename
            )
            self.devices_obj[self.specific_device].clear_folder('sdcard/DCIM/Camera/')

    def _execute(self):
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

        if self.pull_files_bool:
            self.pull_new_images('before_cases', 'old_image')

        for temp in list(self.lights_seq.keys()):
            if not self.stop_signal:
                break

            self.output_gui(f'\nStarting Color Temp: {temp}')
            lights.turn_on(temp)
            lights.set_brightness(1)

            for lux in self.lights_seq[temp]:
                self.output_gui(f'Doing {lux} lux...')
                lights.set_lux(luxmeter, lux)

                # Do the thing
                if self.specific_device is None:
                    for device in self.attached_devices:
                        self.output_gui(
                            f'Now executing using device {device} ({self.devices_obj[device].friendly_name})'
                        )
                        self.devices_obj[device].take_photo()

                else:
                    self.output_gui(
                        f'Now executing using {self.specific_device} ' +
                        f'({self.devices_obj[self.specific_device].friendly_name})'
                    )
                    self.devices_obj[self.specific_device].take_photo()

                self.progress += progress_step
                # send progress to gui thread
                self.gui_window.write_event_value(
                    self.gui_event,
                    {
                        'progress': self.progress,
                        'error': False
                    }
                )
                if self.pull_files_bool:
                    time.sleep(1)
                    self.pull_new_images(temp, f'{temp}_{lux}')

            self.output_gui(f'{temp} is done! Turning it off.')
            lights.turn_off(temp)

        lights.disconnect()

    def execute(self):
        threading.Thread(target=self._execute, args=(), daemon=True).start()
