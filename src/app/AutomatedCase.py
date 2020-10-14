import os
import time
import threading
import xml.etree.cElementTree as ET
from pathlib import Path

from PySimpleGUI import cprint as gui_print

import src.constants as constants
from src.app.LightsCtrl import LightsCtrl
from src.app.Sensor import Sensor
from src.app.Reports import Report


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
        # super(AutomatedCase, self).__init__()
        threading.Thread.__init__(self)
        self.name = 'AutomatedCasesThread'

        # Class initialization
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

        self.luxmeter_model = luxmeter_model
        self.luxmeter = None

        self.lights_model = lights_model
        self.lights = None

        self.excel_data = None

    def run(self):
        self._run_prereq()

    def _run_prereq(self):
        # Initialize Luxmeter
        self.output_gui("Initializing Luxmeter...")
        self.luxmeter = Sensor(constants.LUXMETERS_MODELS[self.luxmeter_model])
        self.output_gui("Luxmeter Initialized!", msg_type='success')
        # self.output_gui("Unsupported luxmeter selected!", msg_type='error')

        # Initialize Lights
        self.output_gui('Initializing lights...')
        self.lights = LightsCtrl(self.lights_model)  # Create lights object
        self.output_gui("Lights Initialized!", msg_type='success')
        # self.output_gui("Unsupported lights selected!", msg_type='error')

    # def run_prereq(self):
    #     prereq_thread = threading.Thread(
    #         target=self._run_prereq,
    #         args=(),
    #         daemon=True)
    #     prereq_thread.start()

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
                'current_action': self.current_action,
                'is_running': self.is_running
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

    def _execute(self, lights_seq_xml,
                 pull_files_bool: bool, pull_files_location: str,
                 photo_bool: bool, video_bool: bool,
                 specific_device=None, folders: list = None, filename_prefix: str = None,
                 lights_seq_in=None, seq_name=None,
                 video_duration: int = None, single_exec: bool = False) -> dict:
        if lights_seq_xml == '':
            self.output_gui('Lights sequence XML is mandatory!', msg_type='error')
            return
        elif pull_files_bool and pull_files_location == '':
            self.output_gui('Files destination is mandatory!', msg_type='error')
            return
        # TODO add checks for luxmeter and lights
        results = {}
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

        self.current_action = current_action
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
                current_lux = self.lights.set_lux(self.luxmeter, lux)

                # send progress to gui thread
                self.gui_window.write_event_value(
                    self.gui_event,
                    {
                        'progress': self.progress,
                        'error': self.error,
                        'current_action': self.current_action,
                        'is_running': self.is_running
                    }
                )
                if self.stop_signal:
                    self.output_gui('Received stop command! Stopping...')
                    break
                self.output_gui(f'Doing {lux} lux...')
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

                    new_files = self.pull_new_images(
                        # returns a dict with keys being serial nums and each having a value - list of pulled images
                        [temp] if folders is None else folders + [temp],
                        f'{prefix}{temp}_{lux}',
                        specific_device)



                    for serial_num in new_files.keys():
                        try:
                            results[serial_num] += new_files[serial_num]
                        except KeyError:
                            results[serial_num] = new_files[serial_num]

                        # add new_files to self.excel_data[test_type][light][lux]['filename']
                        if self.excel_data is not None:
                            # Lower case and filter all but letters
                            test_type = prefix.strip('_')  # TODO: Not use prefix for this
                            # add filename to excel_data dict
                            self.excel_data[test_type][temp][lux]['filename'] = str(new_files[serial_num][0])

            self.output_gui(f'{temp} is done! Turning it off.', 'success')
            self.lights.turn_off(temp)
            if self.stop_signal:
                self.output_gui('Received stop command! Stopping...')
                self.progress = 0
                break

        if single_exec:
            self.is_running = False
        print('Small Exec Files Result: \n' + str(results))
        return results

    def execute(self, lights_seq_xml,
                pull_files_bool: bool, pull_files_location: str,
                photo_bool: bool, video_bool: bool,
                specific_device=None, folders: list = None, filename_prefix: str = None,
                lights_seq_in=None, seq_name=None,
                video_duration: int = None):
        self.stop_signal = False
        threading.Thread(target=self._execute,
                         args=(lights_seq_xml,
                               pull_files_bool, pull_files_location,
                               photo_bool, video_bool,
                               specific_device, folders, filename_prefix,
                               lights_seq_in, seq_name,
                               video_duration, True),
                         daemon=True).start()

    def _execute_req_template(self,
                              requirements_file, files_destination,
                              reports_bool: bool, reports_pdf_bool: bool, specific_device=None):
        if requirements_file == '':
            self.output_gui('Requirements file is mandatory!', msg_type='error')
            return
        elif files_destination == '':
            self.output_gui('Files destination is mandatory!', msg_type='error')
            return

        self.current_action = 'starting'
        excel_data = Report.parse_excel_template(requirements_file)
        lights_seqs = Report.generate_lights_seqs(excel_data)
        new_files = {}

        # Add filenames to excel_data afterwards
        self.excel_data = excel_data

        # Allocate lists for devices' results data
        if specific_device:
            new_files[specific_device] = []
        else:
            for device_serial in self.attached_devices:
                new_files[device_serial] = []

        # Execute cases and persist data
        for lights_seq in lights_seqs:
            if self.stop_signal:
                self.output_gui('Received stop command! Stopping lights sequences...')
                break
            seq_files_dict = self._execute(
                None,
                True, files_destination,
                photo_bool=True, video_bool=False, specific_device=specific_device,
                folders=[lights_seq['test_type']],
                filename_prefix=lights_seq['test_type'],
                lights_seq_in=lights_seq['lights_seq'],
                seq_name=lights_seq['test_type'])
            if seq_files_dict is not None:
                for device_serial in seq_files_dict.keys():
                    new_files[device_serial].append(
                        {
                            'analysis_type': lights_seq['test_type'],
                            'image_files': seq_files_dict[device_serial]
                        }
                    )
            else:
                print(lights_seq['test_type'], ' is empty, skipping it')
            self.output_gui(f'Test cases for {lights_seq["test_type"]} finished.', 'success')
            self.progress = 0

            print(f'Ecxel data: \n{excel_data}')

        print("New case files from template:\n", new_files)

        print(f'Ecxel data: \n{excel_data}')
        testdict = {'Type1000123456': [{'analysis_type': 'eSFR ISO', 'image_files': ['C:\\Users\\mms00519\\Desktop\\template_testing\\CHINABOY\\eSFR ISO\\D65\\eSFR ISO_D65_20.jpg', 'C:\\Users\\mms00519\\Desktop\\template_testing\\CHINABOY\\eSFR ISO\\D65\\eSFR ISO_D65_80.jpg', 'C:\\Users\\mms00519\\Desktop\\template_testing\\CHINABOY\\eSFR ISO\\D65\\eSFR ISO_D65_200.jpg']}, {'analysis_type': 'Random', 'image_files': ['C:\\Users\\mms00519\\Desktop\\template_testing\\CHINABOY\\Random\\D75\\Random_D75_20.jpg', 'C:\\Users\\mms00519\\Desktop\\template_testing\\CHINABOY\\Random\\D75\\Random_D75_80.jpg', 'C:\\Users\\mms00519\\Desktop\\template_testing\\CHINABOY\\Random\\D75\\Random_D75_200.jpg']}, {'analysis_type': 'Colorcheck', 'image_files': ['C:\\Users\\mms00519\\Desktop\\template_testing\\CHINABOY\\Colorcheck\\D75\\Colorcheck_D75_80.jpg', 'C:\\Users\\mms00519\\Desktop\\template_testing\\CHINABOY\\Colorcheck\\D65\\Colorcheck_D65_20.jpg', 'C:\\Users\\mms00519\\Desktop\\template_testing\\CHINABOY\\Colorcheck\\D65\\Colorcheck_D65_80.jpg', 'C:\\Users\\mms00519\\Desktop\\template_testing\\CHINABOY\\Colorcheck\\D65\\Colorcheck_D65_200.jpg', 'C:\\Users\\mms00519\\Desktop\\template_testing\\CHINABOY\\Colorcheck\\D65\\Colorcheck_D65_1000.jpg']}, {'analysis_type': 'Distortion', 'image_files': ['C:\\Users\\mms00519\\Desktop\\template_testing\\CHINABOY\\Distortion\\D65\\Distortion_D65_80.jpg']}, {'analysis_type': 'Uniformity', 'image_files': ['C:\\Users\\mms00519\\Desktop\\template_testing\\CHINABOY\\Uniformity\\D65\\Uniformity_D65_80.jpg', 'C:\\Users\\mms00519\\Desktop\\template_testing\\CHINABOY\\Uniformity\\D65\\Uniformity_D65_200.jpg']}]}
        print(f'test dict: \n{testdict}')
        ini_file = os.path.normpath(r"C:\Program Files\Imatest\v2020.2\IT\samples\python\ini_file\imatest-v2.ini")

        # for
        # for test_type in excel_data.keys():
        #     list_len = len()
        #     # Filter out special characters and spaces
        #     test_type_clean = ''.join(filter(str.isalnum, test_type.lower()))
        #     for light in excel_data[test_type].keys():
        #         for lux in excel_data[test_type][light].keys():
        #             filename = ''
        #             excel_data[test_type][light][lux]['filename'] = filename

        if self.stop_signal:
            self.output_gui('Received stop command! Stopping template testing...')
            return
        # -- Report (Analyze) --
        if reports_bool:
            # Figure out stuff with ini file

            self.current_action = 'Analyzing Images'
            self.output_gui('Analyzing images...')
            # report = Report()
            # images_analysis = report.analyze_images_parallel(testdict, ini_file, num_processes=4)
            # print('Analysis Results:\n', images_analysis)

            self.current_action = 'Generating Report'
            self.output_gui('Generating report...')

            if reports_pdf_bool:
                # Convert report to pdf
                self.current_action = 'Converting Report to PDF'
                self.output_gui('Converting report to PDF...')

        self.excel_data = None
        self.current_action = 'Finished'
        self.output_gui("Template testing Done!", 'success')

    def execute_req_template(self,
                             requirements_file, files_destination,
                             reports_bool: bool, reports_pdf_bool: bool, specific_device=None):
        self.stop_signal = False
        threading.Thread(target=self._execute_req_template,
                         args=(requirements_file, files_destination,
                               reports_bool, reports_pdf_bool, specific_device),
                         daemon=True).start()
        print('After thread exec in func')

    def __del__(self):
        self.lights.disconnect()
