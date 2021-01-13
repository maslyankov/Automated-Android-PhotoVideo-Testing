import os
import time
import xml.etree.cElementTree as ET
from datetime import datetime
from threading import Thread
from pathlib import Path

from PySimpleGUI import cprint as gui_print

from src import constants
from src.logs import logger
from src.code.LightsCtrl import LightsCtrl
from src.code.devices.Sensor import Sensor

from src.code.utils.utils import analyze_images_test_results
from src.code.utils.excel_tools import export_to_excel_file


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
        logger.error("Lights sequence file nonexistent!")
        return
    except ET.ParseError:
        logger.error("Failed to load Lights sequence file! :( XML Error!")
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


class AutomatedCase(Thread):
    def __init__(self, adb, lights_model, luxmeter_model, gui_window, gui_output, gui_event):
        # super(AutomatedCase, self).__init__()
        Thread.__init__(self)
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
        self.current_action_progress = 0
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
        logger.info("Initializing Luxmeter...")
        self.output_gui("Initializing Luxmeter...")

        self.luxmeter = Sensor(constants.LUXMETERS_MODELS[self.luxmeter_model])

        logger.info(f"Luxmeter {constants.LUXMETERS_MODELS[self.luxmeter_model]} Initialized!")
        self.output_gui("Luxmeter Initialized!", msg_type='success')
        # self.output_gui("Unsupported luxmeter selected!", msg_type='error')

        # Initialize Lights
        logger.info(f"Initializing {self.lights_model} lights...")
        self.output_gui('Initializing lights...')

        self.lights = LightsCtrl(self.lights_model)  # Create lights object

        logger.info(f"Lights {self.lights_model} Initialized!")
        self.output_gui("Lights Initialized!", msg_type='success')
        # self.output_gui("Unsupported lights selected!", msg_type='error')

    # def run_prereq(self):
    #     prereq_thread = Thread(
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
                'current_action_progress': self.current_action_progress,
                'is_running': self.is_running
            }
        )
        gui_print(text, window=self.gui_window, key=self.gui_output, colors=text_color)

    def generate_lights_seqs(self, req_dict=None):
        if not req_dict:
            req_dict = self.template_data

        lights_list = []

        for test_type in req_dict.keys():
            lights_list.append(
                {
                    'test_type': test_type,
                    'lights_seq': {}
                }
            )
            for light_type in req_dict[test_type].keys():
                lights_list[len(lights_list) - 1]['lights_seq'][light_type] = []
                for lux in req_dict[test_type][light_type].keys():
                    lights_list[len(lights_list) - 1]['lights_seq'][light_type].append(lux)

        return lights_list

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

                logger.debug(f"current list of files: {self.devices_obj[device].get_camera_files_list()}")
                self.output_gui(f'Now pulling from device {device} ({self.devices_obj[device].friendly_name})')
                pulled_files[device] = self.devices_obj[device].pull_and_rename(
                    dest,
                    filename
                )
                self.devices_obj[device].clear_folder('sdcard/DCIM/Camera/')
        else:
            logger.debug(f'Now pulling from {specific_device} ({self.devices_obj[specific_device].friendly_name})')
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
            logger.error("Received empty Lights sequence XML!")
            self.output_gui('Lights sequence XML is mandatory!', msg_type='error')
            return
        elif pull_files_bool and pull_files_location == '':
            logger.error("Received empty Files destination!")
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

            logger.debug(f"name: {self.lights_seq_name}\ndesc: {self.lights_seq_desc}")
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
            logger.info(f"Lights Status: \n{lights_status}\n")
            self.output_gui(f"Lights Status: \n{lights_status}\n")

        # Prior to testing, pull files from device and clear it up
        if pull_files_bool:
            self.pull_new_images(
                ['before_cases'] if folders is None else folders + ['before_cases'],
                'old_images',
                specific_device)

        # Begin sequence
        for temp in list(self.lights_seq.keys()):
            logger.info(f'\nStarting Color Temp: {temp}')
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
                    logger.info('Received stop command! Stopping...')
                    self.output_gui('Received stop command! Stopping...')
                    break
                logger.info(f'Doing {lux} lux...')
                logger.info(f'Lux is at {current_lux} lux')
                self.output_gui(f'Doing {lux} lux...')
                self.output_gui(f'Lux is at {current_lux} lux')

                # Do the thing
                if specific_device is None:
                    for device in self.attached_devices:
                        logger.info(f'Now executing using device {device} ({self.devices_obj[device].friendly_name})')
                        self.output_gui(
                            f'Now executing using device {device} ({self.devices_obj[device].friendly_name})'
                        )
                        if photo_bool:
                            self.devices_obj[device].take_photo()
                        if video_bool:
                            self.devices_obj[device].start_video()
                    if video_bool:
                        logger.info(f"Waiting {video_duration} seconds for video to finish")
                        self.output_gui(f"Waiting {video_duration} seconds for video to finish")
                        time.sleep(video_duration)
                        for device in self.attached_devices:
                            logger.info(f'Now stopping video for device {device} ({self.devices_obj[device].friendly_name})')
                            self.output_gui(
                                f'Now stopping video for device {device} ({self.devices_obj[device].friendly_name})'
                            )
                            self.devices_obj[device].stop_video()
                else:
                    logger.info(
                        f'Now executing using {specific_device} ' +
                        f'({self.devices_obj[specific_device].friendly_name})'
                    )
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
                        specific_device
                    )

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
                                logger.error(f'No new file for {test_type}//{temp}//{str(lux)}')
            logger.info(f'{temp} is done! Turning it off.')
            self.output_gui(f'{temp} is done! Turning it off.', 'success')
            self.lights.turn_off(temp)
            if self.stop_signal:
                logger.info('Received stop command! Stopping...')
                self.output_gui('Received stop command! Stopping...')
                self.progress = 0
                break

        if single_exec:
            self.is_running = False

        logger.info("Execution Done!")
        logger.debug('Small Exec Files Result: \n' + str(results))
        return results

    def execute(self, lights_seq_xml,
                pull_files_bool: bool, pull_files_location: str,
                photo_bool: bool, video_bool: bool,
                specific_device=None, folders: list = None, filename_prefix: str = None,
                lights_seq_in=None, seq_name=None,
                video_duration: int = None):
        self.stop_signal = False
        Thread(target=self._execute,
                         args=(lights_seq_xml,
                               pull_files_bool, pull_files_location,
                               photo_bool, video_bool,
                               specific_device, folders, filename_prefix,
                               lights_seq_in, seq_name,
                               video_duration, True),
                         daemon=True).start()

    def _execute_req_template(self,
                              requirements_dict, files_destination,
                              reports_bool: bool, reports_excel_bool: bool, reports_pdf_bool: bool, specific_device=None):
        logger.info("Starting execution of requirements template...")

        if requirements_dict == '':
            logger.error('Received empty Requirements file!')
            self.output_gui('Requirements file is mandatory!', msg_type='error')
            return
        elif files_destination == '':
            logger.error("Received empty Files destination")
            self.output_gui('Files destination is mandatory!', msg_type='error')
            return

        self.current_action = 'starting'
        self.template_data = requirements_dict
        files_destination = os.path.normpath(files_destination)
        files_to_analyze = {}

        lights_seqs = self.generate_lights_seqs()
        logger.debug("Lights Seq: ", lights_seqs)

        # Allocate lists for devices' results data
        if specific_device:
            files_to_analyze[specific_device] = []
        else:
            for device_serial in self.attached_devices:
                files_to_analyze[device_serial] = []

        # # Execute cases and persist data
        # for lights_seq in lights_seqs:
        #     if self.stop_signal:
        #         self.output_gui('Received stop command! Stopping lights sequences...')
        #         break
        #
        #     seq_files_dict = self._execute(
        #         None,
        #         True, files_destination,
        #         photo_bool=True, video_bool=False, specific_device=specific_device,
        #         folders=[lights_seq['test_type']],
        #         filename_prefix=lights_seq['test_type'],
        #         lights_seq_in=lights_seq['lights_seq'],
        #         seq_name=lights_seq['test_type'])
        #
        #     # Add stuff to another dict of image files for analysis
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

        logger.debug(f"New files to analyze from template:\n{files_to_analyze}")
        logger.debug(f'Template data: \n{self.template_data}')

        self.template_data = test_template_data = {'blemish': {'D65': {20: {'params': {'mean_input_pixel_level': {'min': 1.0, 'max': 6.0}}, 'filename': 'C:\\Users\\mms00519\\Desktop\\template_testing\\CHINABOY-example\\blemish\\D65\\blemish_D65_20.jpg'}, 40: {'params': {'mean_input_pixel_level': {'min': 1.0, 'max': 6.0}}, 'filename': 'C:\\Users\\mms00519\\Desktop\\template_testing\\CHINABOY-example\\blemish\\D65\\blemish_D65_40.jpg'}}, 'D75': {60: {'params': {'deadThreshold': {'min': 2.0, 'max': 12.0}, 'nDeadPixels': {'min': 2.0, 'max': 12.0}}, 'filename': 'C:\\Users\\mms00519\\Desktop\\template_testing\\CHINABOY-example\\blemish\\D75\\blemish_D75_60.jpg'}, 80: {'params': {'Optical_center_pixels': {'min': 2.0, 'max': 12.0}, 'hotThreshold': {'min': 1.0, 'max': 10.0}}, 'filename': 'C:\\Users\\mms00519\\Desktop\\template_testing\\CHINABOY-example\\blemish\\D75\\blemish_D75_80.jpg'}}}, 'checkerboard': {'INCA': {80: {'params': {}, 'filename': 'C:\\Users\\mms00519\\Desktop\\template_testing\\CHINABOY-example\\checkerboard\\INCA\\checkerboard_INCA_80.jpg'}, 160: {'params': {'pixel_level_ratio_mean': {'min': 2.0, 'max': 12.0}}, 'filename': 'C:\\Users\\mms00519\\Desktop\\template_testing\\CHINABOY-example\\checkerboard\\INCA\\checkerboard_INCA_160.jpg'}}, 'TL84': {100: {'params': {}, 'filename': 'C:\\Users\\mms00519\\Desktop\\template_testing\\CHINABOY-example\\checkerboard\\TL84\\checkerboard_TL84_100.jpg'}, 200: {'params': {'bayer_error': {'min': 1.0, 'max': 5.0}, 'worst_geometric_distortion_pct': {'min': 1.0, 'max': 5.0}}, 'filename': 'C:\\Users\\mms00519\\Desktop\\template_testing\\CHINABOY-example\\checkerboard\\TL84\\checkerboard_TL84_200.jpg'}}}, 'esfriso': {'D65': {200: {'params': {'Max_Delta_Hue': {'min': 11.0, 'max': 20.0}, 'Mean_Delta_Hue': {'min': 4.0, 'max': 6.0}}, 'filename': 'C:\\Users\\mms00519\\Desktop\\template_testing\\CHINABOY-example\\esfriso\\D65\\esfriso_D65_200.jpg'}, 400: {'params': {'Max_Delta_Chroma': {'min': -1.0, 'max': -5.0}, 'Mean_Delta_Chroma': {'min': -14.0, 'max': -17.0}}, 'filename': 'C:\\Users\\mms00519\\Desktop\\template_testing\\CHINABOY-example\\esfriso\\D65\\esfriso_D65_400.jpg'}, 600: {'params': {'Mean_Delta_L': {'min': 13.0, 'max': 16.0}}, 'filename': 'C:\\Users\\mms00519\\Desktop\\template_testing\\CHINABOY-example\\esfriso\\D65\\esfriso_D65_600.jpg'}}}}
        testdict = {'Type1000123456': [{'analysis_type': 'blemish', 'image_files': ['C:\\Users\\mms00519\\Desktop\\template_testing\\CHINABOY-example\\blemish\\D65\\blemish_D65_20.jpg', 'C:\\Users\\mms00519\\Desktop\\template_testing\\CHINABOY-example\\blemish\\D65\\blemish_D65_40.jpg', 'C:\\Users\\mms00519\\Desktop\\template_testing\\CHINABOY-example\\blemish\\D75\\blemish_D75_60.jpg', 'C:\\Users\\mms00519\\Desktop\\template_testing\\CHINABOY-example\\blemish\\D75\\blemish_D75_80.jpg']}, {'analysis_type': 'checkerboard', 'image_files': ['C:\\Users\\mms00519\\Desktop\\template_testing\\CHINABOY-example\\checkerboard\\INCA\\checkerboard_INCA_80.jpg', 'C:\\Users\\mms00519\\Desktop\\template_testing\\CHINABOY-example\\checkerboard\\INCA\\checkerboard_INCA_160.jpg', 'C:\\Users\\mms00519\\Desktop\\template_testing\\CHINABOY-example\\checkerboard\\TL84\\checkerboard_TL84_100.jpg', 'C:\\Users\\mms00519\\Desktop\\template_testing\\CHINABOY-example\\checkerboard\\TL84\\checkerboard_TL84_200.jpg']}, {'analysis_type': 'esfriso', 'image_files': ['C:\\Users\\mms00519\\Desktop\\template_testing\\CHINABOY-example\\esfriso\\D65\\esfriso_D65_200.jpg', 'C:\\Users\\mms00519\\Desktop\\template_testing\\CHINABOY-example\\esfriso\\D65\\esfriso_D65_400.jpg', 'C:\\Users\\mms00519\\Desktop\\template_testing\\CHINABOY-example\\esfriso\\D65\\esfriso_D65_600.jpg']}]}
        logger.debug(f'test dict: \n{testdict}')
        ini_file = os.path.normpath(r"C:\Program Files\Imatest\v2020.2\IT\samples\python\ini_file\imatest-v2.ini")

        if self.stop_signal:
            logger.info('Received stop command! Stopping template testing...')
            self.output_gui('Received stop command! Stopping template testing...')
            return
        
        # -- Report (Analyze) --
        if reports_bool:
            # Figure out stuff with ini file

            self.current_action = 'Analyzing Images'
            logger.info('Analyzing images...')
            self.output_gui('Analyzing images...')
            # report = Report()
                                         # files_to_analyze
            # report.analyze_images_parallel(testdict, ini_file, num_processes=4)  # Returns (<class 'str'>)
            # This returns only some of the results, will have to use .json files for each image

            # # open output file for writing
            # with open('imatest_results.json', 'w') as outfile:
            #     json.dump(images_analysis_readable, outfile)

            # # Load data from file to save time while debugging
            # with open('imatest_results.json') as json_file:
            #     images_analysis_readable = json.load(json_file)

            self.template_data = test_template_data = {'blemish': {'D65': {20: {'params': {'mean_input_pixel_level': {'min': 1.0, 'max': 6.0, 'result': [0.231, 0.2354, 0.2321, 0.2382, 0.22, 0.2233, 0.226, 0.2251, 0.2221, 0.2299, 0.2248, 0.2244, 0.1943, 0.2274, 0.2251, 0.2251, 0.1424, 0.1441, 0.1437, 0.1416, 0.2232, 0.2208, 0.2196, 0.207, 0.2305, 0.1431, 0.2224, 0.1896, 0.2038, 0.1424, 0.1945, 0.2155, 0.2108, 0.2305, 0.2138, 0.1413, 0.1728, 0.1951, 0.2183, 0.2206, 0.2009, 0.1386, 0.2181, 0.1982, 0.205, 0.1947, 0.2059, 0.1986, 0.23, 0.2146, 0.2058, 0.22, 0.2161, 0.2082, 0.2006, 0.2066, 0.2122, 0.2077, 0.2092, 0.233, 0.1438, 0.1997, 0.2075, 0.1623, 0.1992, 0.1955, 0.1931, 0.1846, 0.217, 0.2093, 0.1416, 0.2022, 0.2119, 0.2209, 0.2214, 0.1744, 0.2219, 0.2, 0.1402, 0.1631, 0.2016, 0.189, 0.2087, 0.2121, 0.2104, 0.2094, 0.2054, 0.2119, 0.1993, 0.2296, 0.1957, 0.1958, 0.1791, 0.2115, 0.1476, 0.1496, 0.2306, 0.221, 0.2315, 0.2198, 0.233, 0.2109, 0.1955, 0.2086, 0.1637, 0.2375, 0.2169, 0.1934, 0.1992, 0.2327, 0.219, 0.2165, 0.2369, 0.2055, 0.2008, 0.1957, 0.1991, 0.2005, 0.1439, 0.1486, 0.1891, 0.221, 0.1979, 0.2069, 0.2067, 0.2206, 0.2238, 0.2148, 0.1795, 0.2076, 0.2152, 0.2193, 0.2291, 0.2079, 0.23, 0.1568, 0.1421, 0.1468, 0.1865, 0.1815, 0.1788, 0.2332, 0.2393, 0.2033, 0.1836, 0.2331, 0.2034, 0.1651, 0.2212, 0.2226, 0.2, 0.1956, 0.2039, 0.2457, 0.1938, 0.2121, 0.2017, 0.1752, 0.2247, 0.1962, 0.2252, 0.212, 0.1512, 0.1481, 0.2221, 0.2307, 0.2011, 0.2156, 0.1829, 0.2128, 0.2196, 0.2067, 0.1981, 0.1943, 0.1896, 0.194, 0.1743, 0.1854, 0.1938, 0.1925, 0.2062, 0.2158, 0.212, 0.224, 0.2193, 0.2231, 0.2119, 0.2046, 0.2313, 0.2255, 0.1937, 0.2066, 0.231, 0.2165, 0.1541, 0.184, 0.261, 0.2533, 0.2081, 0.1367, 0.1837, 0.2088, 0.2171, 0.1622, 0.2461, 0.2445, 0.2065, 0.2067, 0.1754, 0.1862, 0.1976, 0.2249, 0.2277, 0.2298, 0.2157, 0.206, 0.1877, 0.2032, 0.2387, 0.2169, 0.2035, 0.1736, 0.1899, 0.2095, 0.2115, 0.205, 0.1694, 0.1799, 0.1929, 0.2031, 0.2298, 0.2023, 0.2227, 0.2183, 0.2104, 0.1617, 0.1934, 0.2023, 0.2116, 0.2161, 0.1841, 0.2616, 0.2207, 0.2182, 0.1823, 0.1881, 0.2088, 0.1903, 0.2041, 0.1649, 0.151, 0.183, 0.1837, 0.2192, 0.2335, 0.2277, 0.2021, 0.1426, 0.2264, 0.2394, 0.1876, 0.2174, 0.204, 0.1784, 0.1898, 0.1786, 0.1893, 0.1925, 0.2068, 0.2548, 0.1979, 0.2093, 0.2335, 0.2124, 0.227, 0.2035, 0.196, 0.1807, 0.1868, 0.2157, 0.1878, 0.2326, 0.1985, 0.219, 0.2038, 0.1661, 0.2005, 0.2119, 0.208, 0.172, 0.2094, 0.2372, 0.2177, 0.1993, 0.1955, 0.2004, 0.1599, 0.178, 0.1705, 0.1997, 0.2003, 0.2059, 0.2373, 0.229, 0.2358, 0.2165, 0.2005, 0.217, 0.2118, 0.1926, 0.2621, 0.2264, 0.1791, 0.2264, 0.2262, 0.206, 0.21, 0.202, 0.1904, 0.1161, 0.1724, 0.2036, 0.1855, 0.2431, 0.2104, 0.2104, 0.1912, 0.2045, 0.1861, 0.1627, 0.1958, 0.2172, 0.1881, 0.2397, 0.2269, 0.2112, 0.2236, 0.205, 0.2198, 0.2138, 0.189, 0.182, 0.1613, 0.1409, 0.144, 0.1463, 0.1699, 0.2636, 0.2434, 0.2421, 0.1946, 0.1996, 0.1946, 0.215, 0.1996, 0.2016, 0.147, 0.1896, 0.1991, 0.1952, 0.2119, 0.215, 0.1935, 0.2617, 0.2202, 0.1976, 0.2303, 0.2183, 0.2016, 0.2118, 0.1922, 0.1983, 0.1868, 0.1867, 0.1855, 0.199, 0.1958, 0.2041, 0.2064, 0.1883, 0.2004, 0.2127, 0.227, 0.1991, 0.2439, 0.2126, 0.222, 0.1896, 0.1944, 0.191, 0.1486, 0.1584, 0.1832, 0.2084, 0.1957, 0.2361, 0.2522, 0.2604, 0.2405, 0.2393, 0.2163, 0.2198, 0.1427, 0.184, 0.2064, 0.2603, 0.2005, 0.2526, 0.2038, 0.246, 0.2122, 0.2138, 0.1995, 0.1835, 0.2025, 0.1726, 0.1628, 0.1903, 0.2023, 0.2019, 0.2207, 0.2063, 0.1746, 0.1706, 0.1916, 0.214, 0.2021, 0.2047, 0.207, 0.1729, 0.2141, 0.224, 0.2245, 0.2398, 0.2347, 0.212, 0.2326, 0.2059, 0.2194, 0.2145, 0.1985, 0.2072, 0.201, 0.1635, 0.16, 0.1857, 0.1848, 0.1975, 0.1864, 0.1807, 0.2082, 0.1992, 0.2088, 0.2014, 0.2153, 0.2093, 0.2475, 0.2265, 0.2264, 0.215, 0.2055, 0.1646, 0.1536, 0.1752, 0.1925, 0.1918, 0.2097, 0.2005, 0.2134, 0.2386, 0.2277, 0.2423, 0.2191, 0.2165, 0.1759, 0.1517, 0.1667, 0.1469, 0.1725, 0.1918, 0.1862, 0.191, 0.2014, 0.1954, 0.2131, 0.2295, 0.2483, 0.2142, 0.1513, 0.1636, 0.1868, 0.1674, 0.1772, 0.1953, 0.1923, 0.1993, 0.1833, 0.2166, 0.2107, 0.2562, 0.2178, 0.208, 0.2354, 0.2221, 0.2201, 0.2128, 0.1769, 0.198, 0.1461, 0.1709, 0.1816, 0.1989, 0.1999, 0.2048, 0.1981, 0.242, 0.1995, 0.222, 0.2016, 0.2167, 0.2476, 0.2244, 0.2279, 0.2237, 0.2024, 0.2013, 0.2074, 0.1915, 0.1847, 0.1678, 0.1384, 0.1404, 0.1765, 0.197, 0.1992, 0.2118, 0.2144, 0.225, 0.2324, 0.2151, 0.2202, 0.2505, 0.236, 0.215, 0.2255, 0.2264, 0.2138, 0.2113, 0.2089, 0.2007, 0.1485, 0.1564, 0.1813, 0.1676, 0.1813, 0.1901, 0.1952, 0.1904, 0.188, 0.2076, 0.1927, 0.2107, 0.2445, 0.2063, 0.2297, 0.2561, 0.262, 0.2041, 0.22, 0.2325, 0.2018, 0.2207, 0.2212, 0.2065, 0.2054, 0.2018, 0.1644, 0.1618, 0.1602, 0.1834, 0.1747, 0.1658, 0.1977, 0.1897, 0.1995, 0.2475, 0.2166, 0.1968, 0.2394, 0.2107, 0.2139, 0.2313, 0.2471, 0.2301, 0.2379, 0.2354, 0.2049, 0.2007, 0.1756, 0.1454, 0.1778, 0.1843, 0.1815, 0.1885, 0.1758, 0.2169, 0.2242, 0.2423, 0.2152, 0.2127, 0.2514, 0.2157, 0.2356, 0.2272, 0.2355, 0.2079, 0.2036, 0.1992, 0.1982, 0.1965, 0.169, 0.1867, 0.1849, 0.1789, 0.1808, 0.2115, 0.1868, 0.2149, 0.1744, 0.2268, 0.2018, 0.2211, 0.245, 0.2184, 0.2236, 0.2225, 0.2543, 0.2335, 0.2327, 0.218, 0.2221, 0.2356, 0.2202, 0.2193, 0.2172, 0.2076, 0.1992, 0.1552, 0.1562, 0.1689, 0.1874, 0.183, 0.1949, 0.1893, 0.1802, 0.2173, 0.1941, 0.2449, 0.199, 0.2148, 0.2432, 0.2025, 0.2075, 0.2232, 0.2326, 0.2266, 0.2203, 0.2224, 0.2096, 0.1879, 0.2074, 0.1926, 0.1854, 0.1776, 0.1996, 0.1886, 0.2213, 0.1924, 0.214, 0.1988, 0.2211, 0.2526, 0.2466, 0.2464, 0.2332, 0.1985, 0.2223, 0.2294, 0.2134, 0.2054, 0.206, 0.2045, 0.1753, 0.1758, 0.1887, 0.188, 0.191, 0.1872, 0.1953, 0.1963, 0.186, 0.1977, 0.2019, 0.2154, 0.1973, 0.2119, 0.2055, 0.1929, 0.2303, 0.2182, 0.2217, 0.2113, 0.2169, 0.2129, 0.2012, 0.1858, 0.1631, 0.1966, 0.1973, 0.1878, 0.2018, 0.1891, 0.1926, 0.1978, 0.1993, 0.2144, 0.2222, 0.216, 0.2411, 0.2058, 0.2582, 0.2364, 0.2197, 0.242, 0.2245, 0.2123, 0.2002, 0.1881, 0.2285, 0.1985, 0.1905, 0.1797, 0.147, 0.1421, 0.149, 0.1515, 0.1849, 0.1864, 0.1892, 0.1594, 0.2125, 0.222, 0.1661, 0.2212, 0.2494, 0.2198, 0.2244, 0.2619, 0.1974, 0.2375, 0.2285, 0.2362, 0.2306, 0.2399, 0.2313, 0.2237, 0.2229, 0.2084, 0.1935, 0.2078, 0.1916, 0.1613, 0.1723, 0.18, 0.1746, 0.1968, 0.1996, 0.1867, 0.2106, 0.2357, 0.196, 0.1965, 0.2565, 0.2383, 0.2245, 0.2309, 0.2181, 0.2165, 0.2102, 0.2052, 0.2082, 0.202, 0.2052, 0.1725, 0.1418, 0.1707, 0.1919, 0.2024, 0.2033, 0.2055, 0.2106, 0.2273, 0.2173, 0.2225, 0.2203, 0.2406, 0.2027, 0.259, 0.2117, 0.2521, 0.2405, 0.2239, 0.2043, 0.2271, 0.2173, 0.2094, 0.2053, 0.2066, 0.179, 0.1607, 0.1594, 0.1357, 0.1766, 0.1804, 0.1904, 0.1857, 0.1795, 0.194, 0.2179, 0.2176, 0.2407, 0.2244, 0.2202, 0.2405, 0.2517, 0.26, 0.2271, 0.259, 0.214, 0.216, 0.2318, 0.2083, 0.2199, 0.2064, 0.2226, 0.2034, 0.2139, 0.2171, 0.2139, 0.1888, 0.2085, 0.1955, 0.1968, 0.1911, 0.1588, 0.1389, 0.1489, 0.1234, 0.1693, 0.1785, 0.1756, 0.1834, 0.1755, 0.1794, 0.1926, 0.1845, 0.1825, 0.1783, 0.1881, 0.2019, 0.1955, 0.1982, 0.211, 0.2033, 0.1915, 0.227, 0.2069, 0.2601, 0.2146, 0.2406, 0.2523, 0.2416, 0.2199, 0.2448, 0.1995, 0.2191, 0.2338, 0.2304, 0.2237, 0.1996, 0.2008, 0.2254, 0.1929, 0.2094, 0.1829, 0.1633, 0.1831, 0.1824, 0.195, 0.185, 0.1891, 0.2053, 0.2044, 0.2164, 0.2158, 0.2221, 0.2048, 0.202, 0.2591, 0.2256, 0.2507, 0.2179, 0.232, 0.2093, 0.2159, 0.2249, 0.1953, 0.2153, 0.2143, 0.2035, 0.1958, 0.1958, 0.1625, 0.1571, 0.1842, 0.1779, 0.1924, 0.1726, 0.2001, 0.2083, 0.2187, 0.218, 0.1871, 0.2437, 0.2384, 0.2433, 0.2147, 0.2501, 0.2416, 0.2433, 0.2395, 0.2402, 0.2294, 0.2302, 0.2144, 0.2238, 0.2206, 0.2151, 0.2156, 0.2119, 0.195, 0.1972, 0.1994, 0.2106, 0.1862, 0.1802, 0.1939, 0.1666, 0.12, 0.1806, 0.1816, 0.1741, 0.1909, 0.1942, 0.2172, 0.2081, 0.1964, 0.2176, 0.2414, 0.2209, 0.2074, 0.2002, 0.2459, 0.2523, 0.2335, 0.2441, 0.206, 0.2009, 0.2242, 0.198, 0.2052, 0.2148, 0.2174, 0.1995, 0.2171, 0.2075, 0.2075, 0.1995, 0.1672, 0.1597, 0.1512, 0.1593, 0.1654, 0.1764, 0.1715, 0.1812, 0.177, 0.1928, 0.1927, 0.1987, 0.2045, 0.2034, 0.1897, 0.2231, 0.209, 0.2462, 0.1988, 0.2324, 0.189, 0.2257, 0.2489, 0.1753, 0.2403, 0.2218, 0.2287, 0.202, 0.238, 0.2282, 0.2287, 0.2498, 0.216, 0.2234, 0.2293, 0.225, 0.211, 0.2128, 0.1951, 0.171, 0.1626, 0.176, 0.1884, 0.1907, 0.1924, 0.2031, 0.1948, 0.1869, 0.1974, 0.2008, 0.2084, 0.1995, 0.1867, 0.2063, 0.2233, 0.208, 0.199, 0.2151, 0.2273, 0.2106, 0.1965, 0.2095, 0.2208, 0.2236, 0.2364, 0.2382, 0.2131, 0.2458, 0.2403, 0.2417, 0.203, 0.2389, 0.2317, 0.1928, 0.198, 0.2135, 0.2152, 0.1993, 0.1616, 0.1444, 0.1734, 0.1747, 0.1794, 0.1847, 0.1735, 0.1818, 0.1793, 0.1789, 0.186, 0.1925, 0.1985, 0.2135, 0.1877, 0.2096, 0.2253, 0.1715, 0.1998, 0.2077, 0.2062, 0.223, 0.2592, 0.2147, 0.2042, 0.2201, 0.2012, 0.2131, 0.1875, 0.2149, 0.1734, 0.1609, 0.1588, 0.1775, 0.1891, 0.1735, 0.1819, 0.1725, 0.1873, 0.181, 0.1882, 0.1863, 0.202, 0.1949, 0.158, 0.2009, 0.1958, 0.1912, 0.1697, 0.2215, 0.1917, 0.2, 0.2282, 0.2199, 0.2268, 0.1762, 0.2429, 0.2032, 0.2369, 0.2115, 0.2305, 0.2201, 0.2217, 0.2277, 0.1899, 0.2162, 0.2022, 0.2046, 0.1612, 0.1732, 0.1772, 0.176, 0.1701, 0.1733, 0.1807, 0.1858, 0.1828, 0.1781, 0.2089, 0.2196, 0.2153, 0.2267, 0.22, 0.2089, 0.1999, 0.2245, 0.2479, 0.2402, 0.2316, 0.2344, 0.2357, 0.2202, 0.2615, 0.2542, 0.2365, 0.2228, 0.2364, 0.2218, 0.2188, 0.207, 0.1929, 0.1907, 0.1983, 0.2079, 0.1784, 0.1686, 0.1638, 0.1783, 0.1847, 0.1793, 0.1839, 0.1771, 0.1843, 0.1838, 0.195, 0.1947, 0.202, 0.1989, 0.1946, 0.1876, 0.2228, 0.2099, 0.2064, 0.2317, 0.212, 0.2317, 0.2041, 0.1786, 0.2366, 0.2021, 0.2464, 0.2307, 0.2263, 0.2322, 0.2517, 0.2604, 0.241, 0.2208, 0.2552, 0.2541, 0.2325, 0.2359, 0.2466, 0.2078, 0.2119, 0.2054, 0.2256, 0.2293, 0.2189, 0.2224, 0.2163, 0.1879, 0.1565, 0.1573, 0.1677, 0.1798, 0.1802, 0.1725, 0.15, 0.1873, 0.1772, 0.1687, 0.1909, 0.1836, 0.1927, 0.2016, 0.2013, 0.1552, 0.2101, 0.2196, 0.219, 0.2182, 0.1936, 0.2059, 0.2406, 0.2402, 0.214, 0.1919, 0.2158, 0.2101, 0.2257, 0.2127, 0.2039, 0.2247, 0.2302, 0.2517, 0.2381, 0.2406, 0.2346, 0.2308, 0.2095, 0.2327, 0.2396, 0.2448, 0.2349, 0.2194, 0.2398, 0.2207, 0.2244, 0.2169, 0.2218, 0.1949, 0.2117, 0.1924, 0.2055, 0.1949, 0.1959, 0.1342, 0.1691, 0.1803, 0.1777, 0.1827, 0.1958, 0.2167, 0.2031, 0.1993, 0.213, 0.1994, 0.2077, 0.2196, 0.2279, 0.1971, 0.1889, 0.2231, 0.2134, 0.2401, 0.19, 0.1763, 0.2574, 0.2447, 0.1984, 0.2591, 0.2668, 0.2236, 0.2439, 0.2051, 0.2478, 0.2582, 0.2565, 0.242, 0.2425, 0.2029, 0.2417, 0.2136, 0.21, 0.2231, 0.2209, 0.2173, 0.236, 0.2064, 0.2194, 0.2173, 0.1815, 0.2085, 0.2029, 0.1775], 'result_calculated': 0.2050105900151285, 'result_pass_bool': False}}, 'filename': 'C:\\Users\\mms00519\\Desktop\\template_testing\\CHINABOY-example\\blemish\\D65\\blemish_D65_20.jpg'}, 40: {'params': {'mean_input_pixel_level': {'min': 1.0, 'max': 6.0, 'result': [0.231, 0.2354, 0.2321, 0.2382, 0.22, 0.2233, 0.226, 0.2251, 0.2221, 0.2299, 0.2248, 0.2244, 0.1943, 0.2274, 0.2251, 0.2251, 0.1424, 0.1441, 0.1437, 0.1416, 0.2232, 0.2208, 0.2196, 0.207, 0.2305, 0.1431, 0.2224, 0.1896, 0.2038, 0.1424, 0.1945, 0.2155, 0.2108, 0.2305, 0.2138, 0.1413, 0.1728, 0.1951, 0.2183, 0.2206, 0.2009, 0.1386, 0.2181, 0.1982, 0.205, 0.1947, 0.2059, 0.1986, 0.23, 0.2146, 0.2058, 0.22, 0.2161, 0.2082, 0.2006, 0.2066, 0.2122, 0.2077, 0.2092, 0.233, 0.1438, 0.1997, 0.2075, 0.1623, 0.1992, 0.1955, 0.1931, 0.1846, 0.217, 0.2093, 0.1416, 0.2022, 0.2119, 0.2209, 0.2214, 0.1744, 0.2219, 0.2, 0.1402, 0.1631, 0.2016, 0.189, 0.2087, 0.2121, 0.2104, 0.2094, 0.2054, 0.2119, 0.1993, 0.2296, 0.1957, 0.1958, 0.1791, 0.2115, 0.1476, 0.1496, 0.2306, 0.221, 0.2315, 0.2198, 0.233, 0.2109, 0.1955, 0.2086, 0.1637, 0.2375, 0.2169, 0.1934, 0.1992, 0.2327, 0.219, 0.2165, 0.2369, 0.2055, 0.2008, 0.1957, 0.1991, 0.2005, 0.1439, 0.1486, 0.1891, 0.221, 0.1979, 0.2069, 0.2067, 0.2206, 0.2238, 0.2148, 0.1795, 0.2076, 0.2152, 0.2193, 0.2291, 0.2079, 0.23, 0.1568, 0.1421, 0.1468, 0.1865, 0.1815, 0.1788, 0.2332, 0.2393, 0.2033, 0.1836, 0.2331, 0.2034, 0.1651, 0.2212, 0.2226, 0.2, 0.1956, 0.2039, 0.2457, 0.1938, 0.2121, 0.2017, 0.1752, 0.2247, 0.1962, 0.2252, 0.212, 0.1512, 0.1481, 0.2221, 0.2307, 0.2011, 0.2156, 0.1829, 0.2128, 0.2196, 0.2067, 0.1981, 0.1943, 0.1896, 0.194, 0.1743, 0.1854, 0.1938, 0.1925, 0.2062, 0.2158, 0.212, 0.224, 0.2193, 0.2231, 0.2119, 0.2046, 0.2313, 0.2255, 0.1937, 0.2066, 0.231, 0.2165, 0.1541, 0.184, 0.261, 0.2533, 0.2081, 0.1367, 0.1837, 0.2088, 0.2171, 0.1622, 0.2461, 0.2445, 0.2065, 0.2067, 0.1754, 0.1862, 0.1976, 0.2249, 0.2277, 0.2298, 0.2157, 0.206, 0.1877, 0.2032, 0.2387, 0.2169, 0.2035, 0.1736, 0.1899, 0.2095, 0.2115, 0.205, 0.1694, 0.1799, 0.1929, 0.2031, 0.2298, 0.2023, 0.2227, 0.2183, 0.2104, 0.1617, 0.1934, 0.2023, 0.2116, 0.2161, 0.1841, 0.2616, 0.2207, 0.2182, 0.1823, 0.1881, 0.2088, 0.1903, 0.2041, 0.1649, 0.151, 0.183, 0.1837, 0.2192, 0.2335, 0.2277, 0.2021, 0.1426, 0.2264, 0.2394, 0.1876, 0.2174, 0.204, 0.1784, 0.1898, 0.1786, 0.1893, 0.1925, 0.2068, 0.2548, 0.1979, 0.2093, 0.2335, 0.2124, 0.227, 0.2035, 0.196, 0.1807, 0.1868, 0.2157, 0.1878, 0.2326, 0.1985, 0.219, 0.2038, 0.1661, 0.2005, 0.2119, 0.208, 0.172, 0.2094, 0.2372, 0.2177, 0.1993, 0.1955, 0.2004, 0.1599, 0.178, 0.1705, 0.1997, 0.2003, 0.2059, 0.2373, 0.229, 0.2358, 0.2165, 0.2005, 0.217, 0.2118, 0.1926, 0.2621, 0.2264, 0.1791, 0.2264, 0.2262, 0.206, 0.21, 0.202, 0.1904, 0.1161, 0.1724, 0.2036, 0.1855, 0.2431, 0.2104, 0.2104, 0.1912, 0.2045, 0.1861, 0.1627, 0.1958, 0.2172, 0.1881, 0.2397, 0.2269, 0.2112, 0.2236, 0.205, 0.2198, 0.2138, 0.189, 0.182, 0.1613, 0.1409, 0.144, 0.1463, 0.1699, 0.2636, 0.2434, 0.2421, 0.1946, 0.1996, 0.1946, 0.215, 0.1996, 0.2016, 0.147, 0.1896, 0.1991, 0.1952, 0.2119, 0.215, 0.1935, 0.2617, 0.2202, 0.1976, 0.2303, 0.2183, 0.2016, 0.2118, 0.1922, 0.1983, 0.1868, 0.1867, 0.1855, 0.199, 0.1958, 0.2041, 0.2064, 0.1883, 0.2004, 0.2127, 0.227, 0.1991, 0.2439, 0.2126, 0.222, 0.1896, 0.1944, 0.191, 0.1486, 0.1584, 0.1832, 0.2084, 0.1957, 0.2361, 0.2522, 0.2604, 0.2405, 0.2393, 0.2163, 0.2198, 0.1427, 0.184, 0.2064, 0.2603, 0.2005, 0.2526, 0.2038, 0.246, 0.2122, 0.2138, 0.1995, 0.1835, 0.2025, 0.1726, 0.1628, 0.1903, 0.2023, 0.2019, 0.2207, 0.2063, 0.1746, 0.1706, 0.1916, 0.214, 0.2021, 0.2047, 0.207, 0.1729, 0.2141, 0.224, 0.2245, 0.2398, 0.2347, 0.212, 0.2326, 0.2059, 0.2194, 0.2145, 0.1985, 0.2072, 0.201, 0.1635, 0.16, 0.1857, 0.1848, 0.1975, 0.1864, 0.1807, 0.2082, 0.1992, 0.2088, 0.2014, 0.2153, 0.2093, 0.2475, 0.2265, 0.2264, 0.215, 0.2055, 0.1646, 0.1536, 0.1752, 0.1925, 0.1918, 0.2097, 0.2005, 0.2134, 0.2386, 0.2277, 0.2423, 0.2191, 0.2165, 0.1759, 0.1517, 0.1667, 0.1469, 0.1725, 0.1918, 0.1862, 0.191, 0.2014, 0.1954, 0.2131, 0.2295, 0.2483, 0.2142, 0.1513, 0.1636, 0.1868, 0.1674, 0.1772, 0.1953, 0.1923, 0.1993, 0.1833, 0.2166, 0.2107, 0.2562, 0.2178, 0.208, 0.2354, 0.2221, 0.2201, 0.2128, 0.1769, 0.198, 0.1461, 0.1709, 0.1816, 0.1989, 0.1999, 0.2048, 0.1981, 0.242, 0.1995, 0.222, 0.2016, 0.2167, 0.2476, 0.2244, 0.2279, 0.2237, 0.2024, 0.2013, 0.2074, 0.1915, 0.1847, 0.1678, 0.1384, 0.1404, 0.1765, 0.197, 0.1992, 0.2118, 0.2144, 0.225, 0.2324, 0.2151, 0.2202, 0.2505, 0.236, 0.215, 0.2255, 0.2264, 0.2138, 0.2113, 0.2089, 0.2007, 0.1485, 0.1564, 0.1813, 0.1676, 0.1813, 0.1901, 0.1952, 0.1904, 0.188, 0.2076, 0.1927, 0.2107, 0.2445, 0.2063, 0.2297, 0.2561, 0.262, 0.2041, 0.22, 0.2325, 0.2018, 0.2207, 0.2212, 0.2065, 0.2054, 0.2018, 0.1644, 0.1618, 0.1602, 0.1834, 0.1747, 0.1658, 0.1977, 0.1897, 0.1995, 0.2475, 0.2166, 0.1968, 0.2394, 0.2107, 0.2139, 0.2313, 0.2471, 0.2301, 0.2379, 0.2354, 0.2049, 0.2007, 0.1756, 0.1454, 0.1778, 0.1843, 0.1815, 0.1885, 0.1758, 0.2169, 0.2242, 0.2423, 0.2152, 0.2127, 0.2514, 0.2157, 0.2356, 0.2272, 0.2355, 0.2079, 0.2036, 0.1992, 0.1982, 0.1965, 0.169, 0.1867, 0.1849, 0.1789, 0.1808, 0.2115, 0.1868, 0.2149, 0.1744, 0.2268, 0.2018, 0.2211, 0.245, 0.2184, 0.2236, 0.2225, 0.2543, 0.2335, 0.2327, 0.218, 0.2221, 0.2356, 0.2202, 0.2193, 0.2172, 0.2076, 0.1992, 0.1552, 0.1562, 0.1689, 0.1874, 0.183, 0.1949, 0.1893, 0.1802, 0.2173, 0.1941, 0.2449, 0.199, 0.2148, 0.2432, 0.2025, 0.2075, 0.2232, 0.2326, 0.2266, 0.2203, 0.2224, 0.2096, 0.1879, 0.2074, 0.1926, 0.1854, 0.1776, 0.1996, 0.1886, 0.2213, 0.1924, 0.214, 0.1988, 0.2211, 0.2526, 0.2466, 0.2464, 0.2332, 0.1985, 0.2223, 0.2294, 0.2134, 0.2054, 0.206, 0.2045, 0.1753, 0.1758, 0.1887, 0.188, 0.191, 0.1872, 0.1953, 0.1963, 0.186, 0.1977, 0.2019, 0.2154, 0.1973, 0.2119, 0.2055, 0.1929, 0.2303, 0.2182, 0.2217, 0.2113, 0.2169, 0.2129, 0.2012, 0.1858, 0.1631, 0.1966, 0.1973, 0.1878, 0.2018, 0.1891, 0.1926, 0.1978, 0.1993, 0.2144, 0.2222, 0.216, 0.2411, 0.2058, 0.2582, 0.2364, 0.2197, 0.242, 0.2245, 0.2123, 0.2002, 0.1881, 0.2285, 0.1985, 0.1905, 0.1797, 0.147, 0.1421, 0.149, 0.1515, 0.1849, 0.1864, 0.1892, 0.1594, 0.2125, 0.222, 0.1661, 0.2212, 0.2494, 0.2198, 0.2244, 0.2619, 0.1974, 0.2375, 0.2285, 0.2362, 0.2306, 0.2399, 0.2313, 0.2237, 0.2229, 0.2084, 0.1935, 0.2078, 0.1916, 0.1613, 0.1723, 0.18, 0.1746, 0.1968, 0.1996, 0.1867, 0.2106, 0.2357, 0.196, 0.1965, 0.2565, 0.2383, 0.2245, 0.2309, 0.2181, 0.2165, 0.2102, 0.2052, 0.2082, 0.202, 0.2052, 0.1725, 0.1418, 0.1707, 0.1919, 0.2024, 0.2033, 0.2055, 0.2106, 0.2273, 0.2173, 0.2225, 0.2203, 0.2406, 0.2027, 0.259, 0.2117, 0.2521, 0.2405, 0.2239, 0.2043, 0.2271, 0.2173, 0.2094, 0.2053, 0.2066, 0.179, 0.1607, 0.1594, 0.1357, 0.1766, 0.1804, 0.1904, 0.1857, 0.1795, 0.194, 0.2179, 0.2176, 0.2407, 0.2244, 0.2202, 0.2405, 0.2517, 0.26, 0.2271, 0.259, 0.214, 0.216, 0.2318, 0.2083, 0.2199, 0.2064, 0.2226, 0.2034, 0.2139, 0.2171, 0.2139, 0.1888, 0.2085, 0.1955, 0.1968, 0.1911, 0.1588, 0.1389, 0.1489, 0.1234, 0.1693, 0.1785, 0.1756, 0.1834, 0.1755, 0.1794, 0.1926, 0.1845, 0.1825, 0.1783, 0.1881, 0.2019, 0.1955, 0.1982, 0.211, 0.2033, 0.1915, 0.227, 0.2069, 0.2601, 0.2146, 0.2406, 0.2523, 0.2416, 0.2199, 0.2448, 0.1995, 0.2191, 0.2338, 0.2304, 0.2237, 0.1996, 0.2008, 0.2254, 0.1929, 0.2094, 0.1829, 0.1633, 0.1831, 0.1824, 0.195, 0.185, 0.1891, 0.2053, 0.2044, 0.2164, 0.2158, 0.2221, 0.2048, 0.202, 0.2591, 0.2256, 0.2507, 0.2179, 0.232, 0.2093, 0.2159, 0.2249, 0.1953, 0.2153, 0.2143, 0.2035, 0.1958, 0.1958, 0.1625, 0.1571, 0.1842, 0.1779, 0.1924, 0.1726, 0.2001, 0.2083, 0.2187, 0.218, 0.1871, 0.2437, 0.2384, 0.2433, 0.2147, 0.2501, 0.2416, 0.2433, 0.2395, 0.2402, 0.2294, 0.2302, 0.2144, 0.2238, 0.2206, 0.2151, 0.2156, 0.2119, 0.195, 0.1972, 0.1994, 0.2106, 0.1862, 0.1802, 0.1939, 0.1666, 0.12, 0.1806, 0.1816, 0.1741, 0.1909, 0.1942, 0.2172, 0.2081, 0.1964, 0.2176, 0.2414, 0.2209, 0.2074, 0.2002, 0.2459, 0.2523, 0.2335, 0.2441, 0.206, 0.2009, 0.2242, 0.198, 0.2052, 0.2148, 0.2174, 0.1995, 0.2171, 0.2075, 0.2075, 0.1995, 0.1672, 0.1597, 0.1512, 0.1593, 0.1654, 0.1764, 0.1715, 0.1812, 0.177, 0.1928, 0.1927, 0.1987, 0.2045, 0.2034, 0.1897, 0.2231, 0.209, 0.2462, 0.1988, 0.2324, 0.189, 0.2257, 0.2489, 0.1753, 0.2403, 0.2218, 0.2287, 0.202, 0.238, 0.2282, 0.2287, 0.2498, 0.216, 0.2234, 0.2293, 0.225, 0.211, 0.2128, 0.1951, 0.171, 0.1626, 0.176, 0.1884, 0.1907, 0.1924, 0.2031, 0.1948, 0.1869, 0.1974, 0.2008, 0.2084, 0.1995, 0.1867, 0.2063, 0.2233, 0.208, 0.199, 0.2151, 0.2273, 0.2106, 0.1965, 0.2095, 0.2208, 0.2236, 0.2364, 0.2382, 0.2131, 0.2458, 0.2403, 0.2417, 0.203, 0.2389, 0.2317, 0.1928, 0.198, 0.2135, 0.2152, 0.1993, 0.1616, 0.1444, 0.1734, 0.1747, 0.1794, 0.1847, 0.1735, 0.1818, 0.1793, 0.1789, 0.186, 0.1925, 0.1985, 0.2135, 0.1877, 0.2096, 0.2253, 0.1715, 0.1998, 0.2077, 0.2062, 0.223, 0.2592, 0.2147, 0.2042, 0.2201, 0.2012, 0.2131, 0.1875, 0.2149, 0.1734, 0.1609, 0.1588, 0.1775, 0.1891, 0.1735, 0.1819, 0.1725, 0.1873, 0.181, 0.1882, 0.1863, 0.202, 0.1949, 0.158, 0.2009, 0.1958, 0.1912, 0.1697, 0.2215, 0.1917, 0.2, 0.2282, 0.2199, 0.2268, 0.1762, 0.2429, 0.2032, 0.2369, 0.2115, 0.2305, 0.2201, 0.2217, 0.2277, 0.1899, 0.2162, 0.2022, 0.2046, 0.1612, 0.1732, 0.1772, 0.176, 0.1701, 0.1733, 0.1807, 0.1858, 0.1828, 0.1781, 0.2089, 0.2196, 0.2153, 0.2267, 0.22, 0.2089, 0.1999, 0.2245, 0.2479, 0.2402, 0.2316, 0.2344, 0.2357, 0.2202, 0.2615, 0.2542, 0.2365, 0.2228, 0.2364, 0.2218, 0.2188, 0.207, 0.1929, 0.1907, 0.1983, 0.2079, 0.1784, 0.1686, 0.1638, 0.1783, 0.1847, 0.1793, 0.1839, 0.1771, 0.1843, 0.1838, 0.195, 0.1947, 0.202, 0.1989, 0.1946, 0.1876, 0.2228, 0.2099, 0.2064, 0.2317, 0.212, 0.2317, 0.2041, 0.1786, 0.2366, 0.2021, 0.2464, 0.2307, 0.2263, 0.2322, 0.2517, 0.2604, 0.241, 0.2208, 0.2552, 0.2541, 0.2325, 0.2359, 0.2466, 0.2078, 0.2119, 0.2054, 0.2256, 0.2293, 0.2189, 0.2224, 0.2163, 0.1879, 0.1565, 0.1573, 0.1677, 0.1798, 0.1802, 0.1725, 0.15, 0.1873, 0.1772, 0.1687, 0.1909, 0.1836, 0.1927, 0.2016, 0.2013, 0.1552, 0.2101, 0.2196, 0.219, 0.2182, 0.1936, 0.2059, 0.2406, 0.2402, 0.214, 0.1919, 0.2158, 0.2101, 0.2257, 0.2127, 0.2039, 0.2247, 0.2302, 0.2517, 0.2381, 0.2406, 0.2346, 0.2308, 0.2095, 0.2327, 0.2396, 0.2448, 0.2349, 0.2194, 0.2398, 0.2207, 0.2244, 0.2169, 0.2218, 0.1949, 0.2117, 0.1924, 0.2055, 0.1949, 0.1959, 0.1342, 0.1691, 0.1803, 0.1777, 0.1827, 0.1958, 0.2167, 0.2031, 0.1993, 0.213, 0.1994, 0.2077, 0.2196, 0.2279, 0.1971, 0.1889, 0.2231, 0.2134, 0.2401, 0.19, 0.1763, 0.2574, 0.2447, 0.1984, 0.2591, 0.2668, 0.2236, 0.2439, 0.2051, 0.2478, 0.2582, 0.2565, 0.242, 0.2425, 0.2029, 0.2417, 0.2136, 0.21, 0.2231, 0.2209, 0.2173, 0.236, 0.2064, 0.2194, 0.2173, 0.1815, 0.2085, 0.2029, 0.1775], 'result_calculated': 0.2050105900151285, 'result_pass_bool': False}}, 'filename': 'C:\\Users\\mms00519\\Desktop\\template_testing\\CHINABOY-example\\blemish\\D65\\blemish_D65_40.jpg'}}, 'D75': {60: {'params': {'deadThreshold': {'min': 2.0, 'max': 12.0, 'result': [4], 'result_calculated': 4.0, 'result_pass_bool': True}, 'nDeadPixels': {'min': 2.0, 'max': 12.0, 'result': [0], 'result_calculated': 0.0, 'result_pass_bool': False}}, 'filename': 'C:\\Users\\mms00519\\Desktop\\template_testing\\CHINABOY-example\\blemish\\D75\\blemish_D75_60.jpg'}, 80: {'params': {'Optical_center_pixels': {'min': 2.0, 'max': 12.0, 'result': [1838.59, 1201.68], 'result_calculated': 1520.135, 'result_pass_bool': False}, 'hotThreshold': {'min': 1.0, 'max': 10.0, 'result': [251], 'result_calculated': 251.0, 'result_pass_bool': False}}, 'filename': 'C:\\Users\\mms00519\\Desktop\\template_testing\\CHINABOY-example\\blemish\\D75\\blemish_D75_80.jpg'}}}, 'checkerboard': {'INCA': {80: {'params': {}, 'filename': 'C:\\Users\\mms00519\\Desktop\\template_testing\\CHINABOY-example\\checkerboard\\INCA\\checkerboard_INCA_80.jpg'}, 160: {'params': {'pixel_level_ratio_mean': {'min': 2.0, 'max': 12.0, 'result': [23.28], 'result_calculated': 23.28, 'result_pass_bool': False}}, 'filename': 'C:\\Users\\mms00519\\Desktop\\template_testing\\CHINABOY-example\\checkerboard\\INCA\\checkerboard_INCA_160.jpg'}}, 'TL84': {100: {'params': {}, 'filename': 'C:\\Users\\mms00519\\Desktop\\template_testing\\CHINABOY-example\\checkerboard\\TL84\\checkerboard_TL84_100.jpg'}, 200: {'params': {'bayer_error': {'min': 1.0, 'max': 5.0, 'result': [0], 'result_calculated': 0.0, 'result_pass_bool': False}, 'worst_geometric_distortion_pct': {'min': 1.0, 'max': 5.0, 'result': [0.5659], 'result_calculated': 0.5659, 'result_pass_bool': False}}, 'filename': 'C:\\Users\\mms00519\\Desktop\\template_testing\\CHINABOY-example\\checkerboard\\TL84\\checkerboard_TL84_200.jpg'}}}, 'esfriso': {'D65': {200: {'params': {'Max_Delta_Hue': {'min': 11.0, 'max': 20.0, 'result': [15.69], 'result_calculated': 15.69, 'result_pass_bool': True}, 'Mean_Delta_Hue': {'min': 4.0, 'max': 6.0, 'result': [5.53], 'result_calculated': 5.53, 'result_pass_bool': True}}, 'filename': 'C:\\Users\\mms00519\\Desktop\\template_testing\\CHINABOY-example\\esfriso\\D65\\esfriso_D65_200.jpg'}, 400: {'params': {'Max_Delta_Chroma': {'min': -1.0, 'max': -5.0, 'result': [-2.58], 'result_calculated': -2.58, 'result_pass_bool': False}, 'Mean_Delta_Chroma': {'min': -14.0, 'max': -17.0, 'result': [-15.74], 'result_calculated': -15.74, 'result_pass_bool': False}}, 'filename': 'C:\\Users\\mms00519\\Desktop\\template_testing\\CHINABOY-example\\esfriso\\D65\\esfriso_D65_400.jpg'}, 600: {'params': {'Mean_Delta_L': {'min': 13.0, 'max': 16.0, 'result': [13.39], 'result_calculated': 13.39, 'result_pass_bool': True}}, 'filename': 'C:\\Users\\mms00519\\Desktop\\template_testing\\CHINABOY-example\\esfriso\\D65\\esfriso_D65_600.jpg'}}}}

            self.current_action = 'Generating Report'
            logger.info('Generating report...')
            self.output_gui('Generating report...')

            # Use images analysis data and insert it into self.template_data dict
            analyze_images_test_results(self.template_data)  # self.template_data
            logger.debug(f'returned: {self.template_data}')

            report_filename = (
                    'Report_' +
                    f'{self.devices_obj[self.attached_devices[0]].friendly_name}_' +  # Device friendly name
                    datetime.now().strftime("%Y%m%d-%H%M%S")
            )

            if reports_excel_bool:
                # Export report to Excel
                self.current_action = 'Exporting Report to Excel'
                logger.info('Exporting report to PDF...')
                self.output_gui('Exporting report to PDF...')

                excel_filename = report_filename + '.xlsx'
                excel_file_path = os.path.join(
                    files_destination,
                    excel_filename
                )
                # Pass template data with analysis results and requirements
                export_to_excel_file(self.template_data, excel_file_path, add_images_bool = False)  # self.template_data
                self.output_gui(f'Excel file exported!\n{excel_file_path}', 'success')

                if reports_pdf_bool:
                    # Convert report to pdf
                    self.current_action = 'Converting Report to PDF'
                    logger.info('Converting report to PDF...')
                    self.output_gui('Converting report to PDF...')

                    pdf_filename = report_filename + '.pdf'
                    pdf_file_path = os.path.join(
                        files_destination,
                        excel_filename
                    )
                    logger.info('PDF file exported!')
                    self.output_gui('PDF file exported!', 'success')

        self.template_data = None
        self.current_action = 'Finished'
        logger.info("Template testing Done!")
        self.output_gui("Template testing Done!", 'success')

    def execute_req_template(self,
                             requirements_dict, files_destination,
                             reports_bool: bool, reports_excel_bool: bool, reports_pdf_bool: bool,
                             specific_device=None):
        self.stop_signal = False
        Thread(target=self._execute_req_template,
                         args=(requirements_dict, files_destination,
                               reports_bool, reports_excel_bool, reports_pdf_bool,
                               specific_device),
                         daemon=True).start()
        logger.info('Requirements template Thread Started!')

    def __del__(self):
        self.lights.disconnect()
