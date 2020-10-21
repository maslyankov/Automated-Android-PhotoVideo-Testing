import json
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
    for elem in root:
        for subelem in elem:
            if subelem.tag == 'sequence':
                # Each color temp
                seq[subelem.attrib["color_temp"]] = []  # New dict key for light temp
                for data in subelem:
                    # Each LUX value
                    seq[subelem.attrib["color_temp"]].append(int(data.text.strip()))  # Add lux to list for light temp
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

        self.template_data = None

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
        results = {}
        self.is_running = True
        self.pull_files_location = pull_files_location

        if lights_seq_in is None:
            # Parse lights seq XML
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
                        if self.template_data is not None:
                            # Lower case and filter all but letters
                            test_type = prefix.strip('_')  # TODO: Not use prefix for this
                            # add filename to excel_data dict
                            try:
                                self.template_data[test_type][temp][lux]['filename'] = str(new_files[serial_num][0])
                            except IndexError:
                                print(f'No new file for {test_type}//{temp}//{str(lux)}')

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
                              requirements_dict, files_destination,
                              reports_bool: bool, reports_pdf_bool: bool, specific_device=None):
        # if requirements_dict == '':
        #     self.output_gui('Requirements file is mandatory!', msg_type='error')
        #     return
        # elif files_destination == '':
        #     self.output_gui('Files destination is mandatory!', msg_type='error')
        #     return

        self.current_action = 'starting'
        template_data = requirements_dict
        lights_seqs = Report.generate_lights_seqs(template_data)
        print("Lights Seq: ", lights_seqs)
        # files_to_analyze = {}
        #
        # # Add filenames to template_data afterwards
        # self.template_data = template_data
        #
        # # Allocate lists for devices' results data
        # if specific_device:
        #     files_to_analyze[specific_device] = []
        # else:
        #     for device_serial in self.attached_devices:
        #         files_to_analyze[device_serial] = []
        #
        # # Execute cases and persist data
        # for lights_seq in lights_seqs:
        #     if self.stop_signal:
        #         self.output_gui('Received stop command! Stopping lights sequences...')
        #         break
        #     seq_files_dict = self._execute(
        #         None,
        #         True, files_destination,
        #         photo_bool=True, video_bool=False, specific_device=specific_device,
        #         folders=[lights_seq['test_type']],
        #         filename_prefix=lights_seq['test_type'],
        #         lights_seq_in=lights_seq['lights_seq'],
        #         seq_name=lights_seq['test_type'])
        #     if seq_files_dict is not None:
        #         for device_serial in seq_files_dict.keys():
        #             files_to_analyze[device_serial].append(
        #                 {
        #                     'analysis_type': lights_seq['test_type'],
        #                     'image_files': seq_files_dict[device_serial]
        #                 }
        #             )
        #     else:
        #         print(lights_seq['test_type'], ' is empty, skipping it')
        #     self.output_gui(f'Test cases for {lights_seq["test_type"]} finished.', 'success')
        #     self.progress = 0
        #
        # print("New files to analyze from template:\n", files_to_analyze)
        # print(f'Template data: \n{template_data}')

        test_template_data = {'eSFR ISO': {'D65': {20: {'params': {'mtf30': {'min': 0.3, 'max': 0.8}, 'oversharpening': {'min': 0, 'max': 30}}, 'filename': 'C:\\Users\\mms00519\\Desktop\\template_testing\\CHINABOY\\eSFR ISO\\D65\\eSFR ISO_D65_20.jpg'}, 80: {'params': {'mtf30': {'min': 0.3, 'max': 0.8}, 'oversharpening': {'min': 0, 'max': 30}, 'ER': {'min': 0, 'max': 0.1}}, 'filename': 'C:\\Users\\mms00519\\Desktop\\template_testing\\CHINABOY\\eSFR ISO\\D65\\eSFR ISO_D65_80.jpg'}, 200: {'params': {'mtf30': {'min': 0.3, 'max': 0.8}, 'oversharpening': {'min': 0, 'max': 30}, 'ER': {'min': 0, 'max': 0.1}}, 'filename': 'C:\\Users\\mms00519\\Desktop\\template_testing\\CHINABOY\\eSFR ISO\\D65\\eSFR ISO_D65_200.jpg'}}}, 'Random': {'D75': {20: {'params': {'Texture Acutance': {'min': 0.7, 'max': 1}}, 'filename': 'C:\\Users\\mms00519\\Desktop\\template_testing\\CHINABOY\\Random\\D75\\Random_D75_20.jpg'}, 80: {'params': {'Texture Acutance': {'min': 0.7, 'max': 1}}, 'filename': 'C:\\Users\\mms00519\\Desktop\\template_testing\\CHINABOY\\Random\\D75\\Random_D75_80.jpg'}, 200: {'params': {'Texture Acutance': {'min': 0.7, 'max': 1}}, 'filename': 'C:\\Users\\mms00519\\Desktop\\template_testing\\CHINABOY\\Random\\D75\\Random_D75_200.jpg'}}}, 'ITDR-36Chart': {}, 'Colorcheck': {'D75': {80: {'params': {'accuracy max': {'min': None, 'max': None}, 'accuracy mean': {'min': None, 'max': None}, 'saturation': {'min': 85, 'max': 135}, 'white balance': {'min': None, 'max': None}}, 'filename': 'C:\\Users\\mms00519\\Desktop\\template_testing\\CHINABOY\\Colorcheck\\D75\\Colorcheck_D75_80.jpg'}}, 'D65': {20: {'params': {'SNR': {'min': 30, 'max': 100}, 'TNR': {'min': 30, 'max': 100}}, 'filename': 'C:\\Users\\mms00519\\Desktop\\template_testing\\CHINABOY\\Colorcheck\\D65\\Colorcheck_D65_20.jpg'}, 80: {'params': {'exposure': {'min': 92, 'max': 162}, 'SNR': {'min': 33, 'max': 100}, 'TNR': {'min': 33, 'max': 100}}, 'filename': 'C:\\Users\\mms00519\\Desktop\\template_testing\\CHINABOY\\Colorcheck\\D65\\Colorcheck_D65_80.jpg'}, 200: {'params': {'accuracy max': {'min': None, 'max': None}, 'accuracy mean': {'min': None, 'max': None}, 'saturation': {'min': 85, 'max': 135}, 'white balance': {'min': None, 'max': None}, 'exposure': {'min': 92, 'max': 162}, 'gamma': {'min': 0.4, 'max': 0.75}, 'SNR': {'min': 38, 'max': 100}, 'TNR': {'min': 38, 'max': 100}}, 'filename': 'C:\\Users\\mms00519\\Desktop\\template_testing\\CHINABOY\\Colorcheck\\D65\\Colorcheck_D65_200.jpg'}, 1000: {'params': {'exposure': {'min': 92, 'max': 162}}, 'filename': 'C:\\Users\\mms00519\\Desktop\\template_testing\\CHINABOY\\Colorcheck\\D65\\Colorcheck_D65_1000.jpg'}}}, 'Distortion': {'D65': {80: {'params': {'35 to 45 deg': {'min': 0, 'max': 6}, '46 to 65': {'min': 0, 'max': 10}, 65: {'min': 0, 'max': 14}}, 'filename': 'C:\\Users\\mms00519\\Desktop\\template_testing\\CHINABOY\\Distortion\\D65\\Distortion_D65_80.jpg'}}}, 'Uniformity': {'D65': {80: {'params': {'Relative Illumination': {'min': 70, 'max': 100}}, 'filename': 'C:\\Users\\mms00519\\Desktop\\template_testing\\CHINABOY\\Uniformity\\D65\\Uniformity_D65_80.jpg'}, 200: {'params': {'Color uniformity': {'min': 0, 'max': 10}, 'Veiling glare': {'min': 0, 'max': 10}}, 'filename': 'C:\\Users\\mms00519\\Desktop\\template_testing\\CHINABOY\\Uniformity\\D65\\Uniformity_D65_200.jpg'}}}}
        testdict = {'Type1000123456': [{'analysis_type': 'eSFR ISO', 'image_files': ['C:\\Users\\mms00519\\Desktop\\template_testing\\CHINABOY\\eSFR ISO\\D65\\eSFR ISO_D65_20.jpg', 'C:\\Users\\mms00519\\Desktop\\template_testing\\CHINABOY\\eSFR ISO\\D65\\eSFR ISO_D65_80.jpg', 'C:\\Users\\mms00519\\Desktop\\template_testing\\CHINABOY\\eSFR ISO\\D65\\eSFR ISO_D65_200.jpg']}, {'analysis_type': 'Random', 'image_files': ['C:\\Users\\mms00519\\Desktop\\template_testing\\CHINABOY\\Random\\D75\\Random_D75_20.jpg', 'C:\\Users\\mms00519\\Desktop\\template_testing\\CHINABOY\\Random\\D75\\Random_D75_80.jpg', 'C:\\Users\\mms00519\\Desktop\\template_testing\\CHINABOY\\Random\\D75\\Random_D75_200.jpg']}, {'analysis_type': 'Colorcheck', 'image_files': ['C:\\Users\\mms00519\\Desktop\\template_testing\\CHINABOY\\Colorcheck\\D75\\Colorcheck_D75_80.jpg', 'C:\\Users\\mms00519\\Desktop\\template_testing\\CHINABOY\\Colorcheck\\D65\\Colorcheck_D65_20.jpg', 'C:\\Users\\mms00519\\Desktop\\template_testing\\CHINABOY\\Colorcheck\\D65\\Colorcheck_D65_80.jpg', 'C:\\Users\\mms00519\\Desktop\\template_testing\\CHINABOY\\Colorcheck\\D65\\Colorcheck_D65_200.jpg', 'C:\\Users\\mms00519\\Desktop\\template_testing\\CHINABOY\\Colorcheck\\D65\\Colorcheck_D65_1000.jpg']}, {'analysis_type': 'Distortion', 'image_files': ['C:\\Users\\mms00519\\Desktop\\template_testing\\CHINABOY\\Distortion\\D65\\Distortion_D65_80.jpg']}, {'analysis_type': 'Uniformity', 'image_files': ['C:\\Users\\mms00519\\Desktop\\template_testing\\CHINABOY\\Uniformity\\D65\\Uniformity_D65_80.jpg', 'C:\\Users\\mms00519\\Desktop\\template_testing\\CHINABOY\\Uniformity\\D65\\Uniformity_D65_200.jpg']}]}
        print(f'test dict: \n{testdict}')
        ini_file = os.path.normpath(r"C:\Program Files\Imatest\v2020.2\IT\samples\python\ini_file\imatest-v2.ini")

        if self.stop_signal:
            self.output_gui('Received stop command! Stopping template testing...')
            return
        # -- Report (Analyze) --
        if reports_bool:
            # Figure out stuff with ini file

            self.current_action = 'Analyzing Images'
            self.output_gui('Analyzing images...')
            # report = Report()
            # images_analysis = report.analyze_images_parallel(testdict, ini_file, num_processes=4)  # Returns (<class 'str'>)
            #
            # images_analysis_readable = json.loads(images_analysis)
            # # open output file for writing
            # with open('imatest_results.json', 'w') as outfile:
            #     json.dump(images_analysis_readable, outfile)

            # Load data from file to save time while debugging
            with open('imatest_results.json') as json_file:
                images_analysis_readable = json.load(json_file)

            # print(f'Analysis Results of type ({type(images_analysis)}):\n', images_analysis)
            print('Parsed:\n', images_analysis_readable)

            self.current_action = 'Generating Report'
            self.output_gui('Generating report...')

            # Decode JSONs
            print('Converting jsons list to dict')
            jsons_dict = {}
            for test_results in images_analysis_readable:
                print('data>title:\n', test_results['data']['title'])
                jsons_dict[test_results['data']['title'].split('.')[0]] = test_results['data']
            print('jsons dict starts:\n', jsons_dict,'\n\n\n----')

            for test_type in test_template_data.keys():
                for light_temp in test_template_data[test_type].keys():
                    for lux in test_template_data[test_type][light_temp].keys():
                        for param in test_template_data[test_type][light_temp][lux]['params'].keys():
                            print(jsons_dict[f'{test_type}_{light_temp}_{lux}'][param])
                            # if test_results["data"]["image_path_name"] == test_template_data[test_type][light_temp]['filename']:
                            #     for param in test_results["data"]

            if reports_pdf_bool:
                # Convert report to pdf
                self.current_action = 'Converting Report to PDF'
                self.output_gui('Converting report to PDF...')

        self.template_data = None
        self.current_action = 'Finished'
        self.output_gui("Template testing Done!", 'success')

    def execute_req_template(self,
                             requirements_dict, files_destination,
                             reports_bool: bool, reports_pdf_bool: bool, specific_device=None):
        self.stop_signal = False
        threading.Thread(target=self._execute_req_template,
                         args=(requirements_dict, files_destination,
                               reports_bool, reports_pdf_bool, specific_device),
                         daemon=True).start()
        print('After thread exec in func')

    def __del__(self):
        self.lights.disconnect()
