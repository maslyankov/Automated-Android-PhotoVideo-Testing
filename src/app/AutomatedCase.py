import os
import time
import threading
import xml.etree.cElementTree as ET
from pathlib import Path

from PySimpleGUI import cprint as gui_print

import src.constants as constants
from src.app.LightsCtrl import LightsCtrl
from src.konica.ChromaMeterKonica import ChromaMeterKonica
from src.app.Reports import Report, parse_excel_template, generate_lights_seqs


def dict_len(dictionary):
    res = 0
    for item in dictionary.keys():
        res += len(dictionary[item])
    return res


def parse_lights_xml_seq(seq_xml):
    seq_name = None
    seq_desc = None
    seq = {}

    try:
        tree = ET.parse(seq_xml)
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
                seq[subelem.attrib["color_temp"]] = []  # New dict key for light temp
                for data in subelem:
                    # Each LUX value
                    seq[subelem.attrib["color_temp"]].append(int(data.text.strip()))  # Add lux to list for light temp

                counter += 1
            elif subelem.tag == 'name':
                seq_name = subelem.text  # Seq Name
            elif subelem.tag == 'description':
                seq_desc = subelem.text  # Seq Description
            else:
                print(f"{subelem.tag}: ", subelem.text)  # Print if there is sth else

    return seq_name, seq_desc, seq


class AutomatedCase(threading.Thread):
    def __init__(self, adb, lights_model, luxmeter_model, gui_window, gui_output, gui_event):

        super().__init__()
        self.attached_devices = adb.attached_devices
        self.devices_obj = adb.devices_obj

        self.pull_files_location = None

        self.gui_window = gui_window
        self.gui_output = gui_output
        self.gui_event = gui_event

        self.lights_seq = {}
        self.lights_seq_name = None
        self.lights_seq_desc = None

        self.is_running = False
        self.stop_signal = False

        self.current_action = None
        self.progress = 0
        self.error = False

        # Initialize Luxmeter
        if luxmeter_model == 'Konita Minolta CL-200A':  # Konita Minolta CL-200A Selected
            self.output_gui("Initializing Luxmeter...")
            self.luxmeter = ChromaMeterKonica()
            self.output_gui("Luxmeter Initialized!", msg_type='success')
        else:
            self.output_gui("Unsupported luxmeter selected!", msg_type='error')
            self.luxmeter = None

        # Initialize Lights
        self.lights_model = lights_model
        self.output_gui('Initializing lights...')
        self.lights = LightsCtrl(lights_model)  # Create lights object
        self.output_gui("Lights Initialized!", msg_type='success')

    def output_gui(self, text, msg_type=None):
        if msg_type == 'error':
            text_color = 'white on red'
            self.error = True
        elif msg_type == 'success':
            text_color = 'white on green'
        else:
            text_color = None

        self.gui_window.write_event_value(
            self.gui_event,
            {
                'progress': self.progress,
                'error': self.error,
                'current_action': self.current_action
            }
        )
        gui_print(text, window=self.gui_window, key=self.gui_output, colors=text_color)

    def pull_new_images(self, folders: list, filename, specific_device=None):
        if self.pull_files_location is None:
            return

        pulled_files = {}

        if specific_device is None:
            for device in self.attached_devices:
                dest = os.path.join(
                    os.path.normpath(self.pull_files_location),
                    self.devices_obj[device].friendly_name,
                    *folders)
                Path(dest).mkdir(parents=True, exist_ok=True)

                print("current list of files: ", self.devices_obj[device].get_camera_files_list())
                self.output_gui(f'Now pulling from device {device} ({self.devices_obj[device].friendly_name})')
                pulled_files[device] = self.devices_obj[device].pull_and_rename(
                    dest,
                    filename
                )
                self.devices_obj[device].clear_folder('sdcard/DCIM/Camera/')
        else:
            self.output_gui(
                f'Now pulling from {specific_device} ({self.devices_obj[specific_device].friendly_name})'
            )
            pulled_files[specific_device] = self.devices_obj[specific_device].pull_and_rename(
                os.path.join(
                    os.path.normpath(self.pull_files_location),
                    self.devices_obj[specific_device].friendly_name,
                    *folders
                ),
                filename
            )
            self.devices_obj[specific_device].clear_folder('sdcard/DCIM/Camera/')

        return pulled_files

    def execute(self, lights_seq_xml,
                pull_files_bool: bool, pull_files_location: str,
                photo_bool: bool, video_bool: bool,
                specific_device=None, folders: list = None, filename_prefix: str = None,
                lights_seq_in=None, seq_name=None,
                video_duration: int = None):
        if lights_seq_xml == '':
            self.output_gui('Lights sequence XML is mandatory!', msg_type='error')
            return
        elif pull_files_location == '':
            self.output_gui('Files destination is mandatory!', msg_type='error')
            return

        self.is_running = True
        self.pull_files_location = pull_files_location

        if lights_seq_in is None:
            lights_seq_xml = os.path.join(constants.ROOT_DIR, 'lights_seq', f'{lights_seq_xml}.xml')

            lights_seq = parse_lights_xml_seq(lights_seq_xml)
            self.lights_seq_name = lights_seq[0]
            current_action = lights_seq[0]
            self.lights_seq_desc = lights_seq[1]
            self.lights_seq = lights_seq[2]
            self.output_gui(f"name: {self.lights_seq_name}\ndesc: {self.lights_seq_desc}")
        else:
            self.lights_seq = lights_seq_in
            current_action = seq_name

        # Check if passed sequence is not empty...
        d_len = dict_len(self.lights_seq)
        if d_len == 0:
            return
        progress_step = 100 / d_len

        # Get lights status
        if self.lights_model == 'SpectriWave':  # SpectriWave Specific
            time.sleep(1)
            lights_status = self.lights.status()
            self.output_gui(f"Lights Status: \n{lights_status}\n")

        # Prior to testing, pull files from device and clear it up
        if pull_files_bool:
            self.pull_new_images(
                ['before_cases'] if folders is None else folders + ['before_cases'],
                'old_images',
                specific_device)

        # Begin sequence
        for temp in list(self.lights_seq.keys()):
            self.output_gui(f'\nStarting Color Temp: {temp}')
            self.lights.turn_on(temp)
            self.lights.set_brightness(1)

            for lux in self.lights_seq[temp]:
                # self.output_gui('Stop signal is ' + str(self.stop_signal))
                if self.stop_signal:
                    self.output_gui('Received stop command! Stopping...')
                    break

                self.current_action = current_action
                # send progress to gui thread
                self.gui_window.write_event_value(
                    self.gui_event,
                    {
                        'progress': self.progress,
                        'error': self.error,
                        'current_action': self.current_action
                    }
                )

                self.output_gui(f'Doing {lux} lux...')
                current_lux = self.lights.set_lux(self.luxmeter, lux)
                self.output_gui(f'Lux is at {current_lux} lux')

                # Do the thing
                if specific_device is None:
                    for device in self.attached_devices:
                        self.output_gui(
                            f'Now executing using device {device} ({self.devices_obj[device].friendly_name})'
                        )
                        if photo_bool:
                            self.devices_obj[device].take_photo()
                        if video_bool:
                            self.devices_obj[device].start_video()
                    if video_bool:
                        self.output_gui(f"Waiting {video_duration} seconds for video to finish")
                        time.sleep(video_duration)
                        for device in self.attached_devices:
                            self.output_gui(
                                f'Now stopping video for device {device} ({self.devices_obj[device].friendly_name})'
                            )
                            self.devices_obj[device].stop_video()
                else:
                    self.output_gui(
                        f'Now executing using {specific_device} ' +
                        f'({self.devices_obj[specific_device].friendly_name})'
                    )
                    if photo_bool:
                        self.devices_obj[specific_device].take_photo()
                    if video_bool:
                        self.devices_obj[specific_device].start_video()
                        time.sleep(video_duration)
                        self.devices_obj[specific_device].stop_video()

                self.progress += progress_step

                # Pull new files and delete them from device
                if pull_files_bool:
                    time.sleep(1)
                    prefix = '' if filename_prefix is None else f"{filename_prefix}_"

                    new_files = self.pull_new_images(  # TODO: Finish up new images persistence
                                    [temp] if folders is None else folders + [temp],
                                    f'{prefix}{temp}_{lux}',
                                    specific_device)

            self.output_gui(f'{temp} is done! Turning it off.', 'success')
            self.lights.turn_off(temp)
            if self.stop_signal:
                self.output_gui('Received stop command! Stopping...')
                break

        self.is_running = False

    # def execute(self, lights_seq_xml,
    #             pull_files_bool: bool, pull_files_location,
    #             photo_bool: bool, video_bool: bool,
    #             specific_device=None, video_duration: int = None, ):
    #     threading.Thread(target=self._execute,
    #                      args=(lights_seq_xml,
    #                            pull_files_bool, pull_files_location,
    #                            photo_bool, video_bool,
    #                            specific_device, video_duration,),
    #                      daemon=True).start()

    def execute_req_template(self,
                             requirements_file, files_destination,
                             reports_bool: bool, reports_pdf_bool: bool, specific_device=None):
        if requirements_file == '':
            self.output_gui('Requirements file is mandatory!', msg_type='error')
            return
        elif files_destination == '':
            self.output_gui('Files destination is mandatory!', msg_type='error')
            return

        excel_data = parse_excel_template(requirements_file)
        lights_seqs = generate_lights_seqs(excel_data)

        for lights_seq in lights_seqs:
            self.execute(None,
                         True, files_destination,
                         photo_bool=True, video_bool=False, specific_device=specific_device,
                         folders=[lights_seq['test_type']],
                         filename_prefix=lights_seq['test_type'],
                         lights_seq_in=lights_seq['lights_seq'],
                         seq_name=lights_seq['test_type'])
            self.output_gui(f'Test cases for {lights_seq["test_type"]} finished.', 'success')

        # -- Report (Analyze) --
        if reports_bool:
            self.current_action = 'Analyzing Images'
            self.output_gui('Analyzing images...')
            # report = Report()
            # report.analyze_images_parallel(images, ini_file, num_processes=4)

            # Figure out stuff with ini file

            self.current_action = 'Generating Report'
            self.output_gui('Generating report...')

            if reports_pdf_bool:
                # Convert report to pdf
                self.current_action = 'Converting Report to PDF'
                self.output_gui('Converting report to PDF...')

    # def execute_req_template(self,
    #                          requirements_file, files_destination,
    #                          reports_bool: bool, reports_pdf_bool: bool, specific_device=None):
    #     print(requirements_file, files_destination, reports_bool, reports_pdf_bool, specific_device)
    #     threading.Thread(target=self._execute_req_template,
    #                      args=(requirements_file, files_destination,
    #                            reports_bool, reports_pdf_bool,
    #                            specific_device,),
    #                      daemon=True).start()

    def __del__(self):
        self.lights.disconnect()
