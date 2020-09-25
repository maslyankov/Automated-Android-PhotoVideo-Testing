import subprocess
import time
import re
import os
import sys
import xml.etree.cElementTree as ET
from natsort import natsorted

import src.constants as constants


# Static Functions
def generate_sequence(subelem):
    seq_temp = []

    for action_num, action in enumerate(subelem):

        action_list = []
        data_list = []

        # self.shoot_photo_seq.append(action.tag)
        for action_elem_num, action_elem in enumerate(action):
            # import pdb; pdb.set_trace()
            print("\naction elem: ", action_elem)
            print("data_list before", data_list)
            if action_elem.tag == 'id':
                action_list.append(action_elem.text)
                print(action_elem_num, action_elem.text)

            elif action_elem.tag == 'description':
                print('description be: ', action_elem.text)
                if action_elem.text is not None:
                    data_list.append(action_elem.text)
                else:
                    data_list.append('')

            elif action_elem.tag == 'coordinates':
                coords_list = []

                for inner_num, inner in enumerate(action_elem):
                    # list should be: self.shoot_photo_seq = [
                    # ['element_id', ['Description', [x, y], 'tap' ] ]
                    # ]
                    coords_list.append(inner.text)
                data_list.append(coords_list)

            elif action_elem.tag == 'value':
                data_list.append(action_elem.text)

            print("data_list after", data_list)
        try:
            data_list.append(action.attrib["type"])  # Set type
        except KeyError:
            print("Error! Invalid XML!")

        action_list.append(data_list)

        seq_temp.append(action_list)
        print('Generated list for action: ', action_list)
    return seq_temp


def xml_from_sequence(obj, prop, xml_obj):
    for action in getattr(obj, prop):
        elem = ET.SubElement(xml_obj, "action")
        elem_id = ET.SubElement(elem, "id")  # set
        elem_desc = ET.SubElement(elem, "description")  # set

        print(action)
        elem.set('type', action[1][2])
        if action[1][2] == 'tap':  # If we have coords set, its a tap action
            elem_coordinates = ET.SubElement(elem, "coordinates")

            x = ET.SubElement(elem_coordinates, "x")  # set
            y = ET.SubElement(elem_coordinates, "y")  # set

            # list should be: self.shoot_photo_seq = [
            # ['element_id', ['Description', [x, y] , type] ]
            # ]
            elem_id.text = str(action[0])
            elem_desc.text = str(action[1][0])
            x.text = str(action[1][1][0])
            y.text = str(action[1][1][1])
        else:
            elem_id.text = str(action[0])
            elem_desc.text = str(action[1][0])
            elem_value = ET.SubElement(elem, "value")
            elem_value.text = str(action[1][1])


# CLASS Device
class Device:
    """
    Class for interacting with devices using adb (ppadb) and AdbClient class
    """

    def __init__(self, adb, device_serial):
        print("Attaching to device...")

        self.adb = adb
        self.adb_client = adb.client
        self.d = self.adb_client.device(device_serial)  # Create device client object
        self.scrcpy = None

        # Object Parameters #
        # Info
        self.device_serial = device_serial  # Assign device serial as received in arguments
        try:
            self.friendly_name = self.get_device_model()
        except RuntimeError:
            print("Device went offline!")

        # Settings
        self.logs_enabled = False
        self.logs_filter = ''
        self.camera_app = None

        # States
        self.current_camera_app_mode = 'photo'
        self.is_recording_video = False

        # Sequences
        self.shoot_photo_seq = []
        self.start_video_seq = []
        self.stop_video_seq = []
        self.goto_photo_seq = []
        self.goto_video_seq = []
        self.actions_time_gap = 1

        self.root()  # Make sure we are using root for device

        # Add device to attached devices list
        adb.attach_device(device_serial, self)

        # Persistence
        self.device_xml = os.path.join(constants.ROOT_DIR, 'settings', f'{device_serial}.xml')

        print("Conn devs: ", adb.attached_devices)  # Debugging
        print("Device Serial: ", device_serial)  # Debugging
        print(f"Device is {self.get_wakefulness()}")

        self.load_settings_file()

        self.print_attributes()

        self.setup_device_settings()
        self.turn_on_and_unlock()

    def root(self):
        """
        Root the device
        :return:None
        """
        print("Rooting device " + self.device_serial)
        root = subprocess.Popen([constants.ADB, '-s', self.device_serial, 'root'],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        stdout, stderr = root.communicate()
        if stderr:
            print("Rooting Errors: {}".format(stderr.decode()))
            print("Exiting in 5 seconds.")
            time.sleep(5)
            exit(1)
        if stdout:
            print("Rooting Output: {}".format(stdout.decode()))
        root.terminate()

    def remount(self):
        """
        Remount the device
        :return:None
        """
        print("Remount device serial: " + self.device_serial)
        remount = subprocess.Popen([constants.ADB, '-s', self.device_serial, 'remount'], stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        stdout, stderr = remount.communicate()
        if stderr:
            print("Remonut Errors: ".format(stderr.decode()))
        if stdout:
            print("Remonut Output: ".format(stdout.decode()))
        remount.terminate()

    def exec_shell(self, cmd):
        """
        Execute a shell command on the device
        :param cmd:String command to execute
        :return:None
        """
        return self.d.shell(cmd)

    def input_tap(self, *coords):  # Send tap events
        """
        Sends tap input to device
        :param coords: tap coordinates to use
        :return:None
        """
        print("X: ", coords[0][0], "Y: ", coords[0][1])  # Debugging
        self.d.shell("input tap {} {}".format(coords[0][0], coords[0][1]))

    def reboot(self):
        """
        Reboots the device.
        :return:None
        """
        self.d.shell("reboot")  # TODO Remove device from connected_devices list after reboot
        # self.adb.detach_device(self.device_serial, self)

    def get_current_app(self):
        """
        Returns currently opened app package and its current activity
        :return:None
        """
        # dumpsys window windows | grep -E 'mFocusedApp' <- had issues with this one, sometimes returns null
        # Alternative -> dumpsys activity | grep top-activity
        try:   # This works on older Android versions
            current = self.d.shell("dumpsys activity | grep -E 'mFocusedActivity'").strip().split(' ')[3].split('/')
            if current is None:
                print('(Get Current App) Focused Activity is empty, trying top-activity...')
                current = self.d.shell("dumpsys activity | grep top-activity").strip().split(' ')[9].split(':')
                temp = current[1].split('/')
                temp.append(current[0])  # -> [pkg, activity_id, pid]
                return temp
        except IndexError:
            print('We had trouble detecting currently opened app! Trying another method!')
            current = self.d.shell("dumpsys window windows | grep -E 'mFocusedApp'").split(' ')[6].split('/')
        return current

    def get_installed_packages(self):
        """
        Get the packages (apps) installed on device
        pm list packages - more widely available than:
        'cmd package list packages -e'
        :return:List of strings, each being an app package on the device
        """
        return sorted(self.d.shell("pm list packages").replace('package:', '').splitlines())

    def open_app(self, package):
        """
        Open an app package
        :param package: Specify the app package that you want to open
        :return:None
        """
        if self.get_current_app() != package:
            print("Opening {}...".format(package))
            self.d.shell("monkey -p '{}' -v 1".format(package))
        else:
            print("{} was already opened! Continuing...".format(package))

    def push_file(self, src, dst):
        """
        Push file to device
        :param src: Path to file to push
        :param dst: Destination on device of file
        :return:None
        """
        self.d.push(src, dst)

    def pull_file(self, src, dst):
        """
        Pull file to device
        :param src: Path on device to file to pull
        :param dst: Destination to save the file to
        :return:None
        """
        self.d.pull(src, dst)

    def get_camera_files_list(self):
        """
        Get a list of files in sdcard/DCIM/Camera on the device
        :return: List of strings, each being a file located in sdcard/DCIM/Camera
        """

        files_list = self.d.shell("ls -1 sdcard/DCIM/Camera").splitlines()
        if files_list[0] == 'ls: sdcard/DCIM/Camera: No such file or directory':  # TODO Fix this shit
            return
        else:
            return files_list

    def clear_folder(self, folder):
        """
        Deletes a folder
        :return:None
        """
        self.d.shell(f"rm -rf {folder}")
        print(f"Deleting folder {folder} from device!")

    def clear_camera_folder(self):
        """
        Deletes camera folder - probably will be deprecated
        :return:None
        """
        self.clear_folder("sdcard/DCIM/Camera/*")

    def has_screen(self):  # TODO Make this return a valid boolean (now it sometimes works, sometimes doesn't)
        """
        Check if the device has an integrated screen (not working all the time)
        :return:Bool Should return a Bool
        """
        before = self.d.shell("dumpsys deviceidle | grep mScreenOn").split('=')[1].strip()
        self.d.shell('input keyevent 26')
        time.sleep(0.5)
        after = self.d.shell("dumpsys deviceidle | grep mScreenOn").split('=')[1].strip()

        if before == after:
            print("Device has no integrated screen!")

        self.d.shell('input keyevent 26')

    def get_screen_resolution(self):
        """
        Get screen resolution of device
        :return:List height and width
        """
        try:
            res = self.d.shell('dumpsys window | grep "mUnrestricted"').strip().split(' ')[1].split('x')
        except IndexError:
            res = self.d.shell('dumpsys window | grep "mUnrestricted"').rstrip().split('][')[1].strip(']').split(',')

        return res

    def get_wakefulness(self):
        return self.d.shell("dumpsys activity | grep -E 'mWakefulness'").split('=')[1]

    def is_sleeping(self):
        state = self.d.shell("dumpsys activity | grep -E 'mSleeping'").strip().split(' ')
        is_sleeping = state[0].split('=')[1]
        try:
            lock_screen = state[1].split('=')[1]
        except IndexError:
            lock_screen = None
        return is_sleeping, lock_screen

    def get_device_model(self):
        """
        Get the device model
        :return: String of device model
        """
        return self.d.shell("getprop ro.product.model").strip()

    def get_device_name(self):
        """
        Get the device name
        :return: String of device name
        """
        return self.d.shell("getprop ro.product.name").strip()

    def get_manufacturer(self):
        return self.d.shell("getprop ro.product.manufacturer").strip()

    def get_board(self):
        return self.d.shell("getprop ro.product.board").strip()

    def get_android_version(self):
        return self.d.shell("getprop ro.build.version.release").strip()

    def get_sdk_version(self):
        return self.d.shell("getprop ro.build.version.sdk").strip()

    def get_cpu(self):
        return self.d.shell("getprop ro.product.cpu.abi").strip()

    def is_adb_enabled(self):
        # Kind of useless as if this is actually false, we will not be able to connect
        return True if self.d.shell('settings get global adb_enabled').strip() == '1' else False

    def setup_device_settings(self):
        print('Making the device an insomniac!')
        self.d.shell('settings put global stay_on_while_plugged_in 1')
        self.d.shell('settings put system screen_off_timeout 9999999')

    def turn_on_and_unlock(self):
        state = self.is_sleeping()
        # print(f"predicate: {state[0] == 'false'}")
        if state[0] == 'true':
            print('Device should have been already turned on')
            self.d.shell('input keyevent 26')  # Event Power Button
            self.d.shell('input keyevent 82')  # Unlock

    def get_device_leds(self):
        """
        Get a list of the leds that the device has
        :return:None
        """
        return natsorted(self.d.shell("ls /sys/class/leds/").strip().replace('\n', '').replace('  ', ' ').split(' '))

    def set_led_color(self, value, led, target):
        """
        Send a value to a led and a target
        ex: /sys/class/leds/RGB1/group_onoff - led is RGB1, target is group_onoff
        :param value: RGB HEX Value to send
        :param led: To which led to send
        :param target: To which target to send
        :return:None
        """
        try:
            self.d.shell('echo {} > /sys/class/leds/{}/{}'.format(value, led, target))
            self.d.shell('echo 60 > /sys/class/leds/{}/global_enable'.format(led))  # Poly
        except RuntimeError:
            print("Device was disconnected before we could detach it properly.. :(")

    def open_device_ctrl(self):
        """
        Open device screen view and control using scrcpy
        :return:None
        """
        print("Opening scrcpy for device ", self.device_serial)
        self.scrcpy = subprocess.Popen([constants.SCRCPY, '--serial', self.device_serial],
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)

    def identify(self):
        """
        Identify device by blinking it's screen or leds
        :return:None
        """
        leds = self.get_device_leds()
        print(leds)  # Debugging
        # Poly
        self.d.shell('echo 1 > /sys/class/leds/{}/global_onoff'.format(leds[0]))

        for k in range(1, 60, 5):  # Blink Leds and screen
            # Poly
            if k != 1:
                time.sleep(0.3)
            self.d.shell('echo {}{}{} > /sys/class/leds/{}/global_enable'.format(k, k, k, leds[0]))  # Poly

            # Devices with screen
            if (k % 11) % 2:
                self.d.shell('input keyevent 26')  # Event Power Button

        self.d.shell('echo 60 > /sys/class/leds/{}/global_enable'.format(leds[0]))  # Poly
        print('Finished identifying!')

    def dump_window_elements(self):
        """
        Dump elements of currently opened app activity window
        and pull them from device to folder XML
        :return:None
        """
        source = self.d.shell('uiautomator dump').split(': ')[1].rstrip()
        current_app = self.get_current_app()
        if source == "null root node returned by UiTestAutomationBridge.":
            print("UIAutomator error! :( Try dumping UI elements again. (It looks like a known error)")
            return

        print('Source returned: ', source)  # Debugging

        self.d.pull(
            source,
            os.path.join(constants.ROOT_DIR,
                         'XML', '{}_{}_{}.xml'.format(self.device_serial, current_app[0], current_app[1]))
        )
        print('Dumped window elements for current app.')

    def get_clickable_window_elements(self, force_dump=False):
        """
        Parse the dumped window elements file and filter only elements that are "clickable"
        :return:Dict key: element_id or number,
                value: String of elem description, touch location (a list of x and y)
        """
        print('Parsing xml...')
        current_app = self.get_current_app()

        if current_app is None:
            print("Current app unknown... We don't know how to name the xml file so we will say NO! :D ")
            return {}

        print("Serial {} , app: {}".format(self.device_serial, current_app))
        file = os.path.join(constants.ROOT_DIR,
                            'XML', '{}_{}_{}.xml'.format(self.device_serial, current_app[0], current_app[1]))

        if force_dump:
            self.dump_window_elements()

        xml_tree = None

        try:
            xml_tree = ET.parse(file)
        except FileNotFoundError:
            print('XML for this UI not found, dumping a new one...')
            self.dump_window_elements()
            xml_tree = ET.parse(file)
        except ET.ParseError as error:
            print("XML Parse Error: ", error)

        try:
            xml_root = xml_tree.getroot()
        except AttributeError:
            print("XML wasn't opened correctly!")
            return
        except UnboundLocalError:
            print("UI Elements XML is probably empty... :( Retrying...")
            self.dump_window_elements()
            xml_tree = ET.parse(file)
            xml_root = xml_tree.getroot()
        elements = {}

        for num, element in enumerate(xml_root.iter("node")):
            elem_res_id = element.attrib['resource-id'].split('/')
            elem_desc = element.attrib['content-desc']
            elem_bounds = re.findall(r'\[([^]]*)]', element.attrib['bounds'])[0].split(',')

            if (elem_res_id or elem_desc) and int(elem_bounds[0]) > 0:
                elem_bounds[0] = int(elem_bounds[0]) + 1
                elem_bounds[1] = int(elem_bounds[1]) + 1
                if elem_res_id[0] != '':
                    try:
                        elements[elem_res_id[1]] = elem_desc, elem_bounds
                    except IndexError:
                        # For elements that don't have an app id as first element
                        elements[elem_res_id[0]] = elem_desc, elem_bounds
                else:
                    elements[num] = elem_desc, elem_bounds

        return elements

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

        root = tree.getroot()
        # all item attributes
        for elem in root:
            for subelem in elem:
                if subelem.tag == 'serial' and subelem.text != self.device_serial:
                    print('XML ERROR! Serial mismatch!')

                if subelem.tag == 'friendly_name':
                    self.friendly_name = subelem.text

                if subelem.tag == 'camera_app':
                    self.camera_app = subelem.text

                if subelem.tag == 'logs':
                    for data in subelem:
                        if data.tag == 'enabled':
                            if data.text == '1':
                                self.logs_enabled = True
                            else:
                                self.logs_enabled = False
                        if data.tag == 'filter':
                            self.logs_filter = data.text if data.text is not None else ''

                for seq_type in list(constants.act_sequences.keys()):
                    if subelem.tag == constants.act_sequences[seq_type]:
                        setattr(self, constants.act_sequences[seq_type], generate_sequence(subelem))
                        print('Obj Seq List: ', getattr(self, constants.act_sequences[seq_type]))

                if subelem.tag == 'actions_time_gap':
                    self.actions_time_gap = int(subelem.text)

    def save_settings(self):
        root = ET.Element('device')

        # Device info
        info = ET.SubElement(root, 'info')

        serial = ET.SubElement(info, "serial")
        serial.text = self.device_serial

        manufacturer = ET.SubElement(info, "manufacturer")
        manufacturer.text = self.get_manufacturer()

        board = ET.SubElement(info, "board")
        board.text = self.get_board()

        name = ET.SubElement(info, "name")
        name.text = self.get_device_name()

        model = ET.SubElement(info, "model")
        model.text = self.get_device_model()

        cpu = ET.SubElement(info, "cpu")
        cpu.text = self.get_cpu()

        resolution = ET.SubElement(info, "screen_resolution")
        res_data = self.get_screen_resolution()
        resolution.text = f'{res_data[0]}x{res_data[1]}'

        android_version = ET.SubElement(info, "android_version")
        android_version.text = self.get_android_version()

        friendly = ET.SubElement(info, "friendly_name")
        friendly.text = self.friendly_name

        # Device settings
        settings = ET.SubElement(root, 'settings')

        cam_app = ET.SubElement(settings, "camera_app")
        cam_app.text = self.camera_app

        logs = ET.SubElement(settings, "logs")

        logs_bool = ET.SubElement(logs, "enabled")
        logs_bool.text = str(1 if self.logs_enabled else 0)

        logs_filter = ET.SubElement(logs, "filter")
        logs_filter.text = self.logs_filter

        for seq_type in list(constants.act_sequences.keys()):
            curr_seq = ET.SubElement(settings, constants.act_sequences[seq_type])
            xml_from_sequence(self, constants.act_sequences[seq_type], curr_seq)

        actions_time_gap = ET.SubElement(settings, "actions_time_gap")
        actions_time_gap.text = str(self.actions_time_gap)

        tree = ET.ElementTree(root)
        print(f'Writing settings to file {self.device_xml}')
        tree.write(self.device_xml, encoding='UTF8', xml_declaration=True)

    def set_logs(self, logs_bool, fltr=None):
        if not isinstance(logs_bool, bool):
            print('Logs setter got a non bool type... Defaulting to False.')
            self.logs_enabled = False
        else:
            self.logs_enabled = logs_bool

        if fltr is not None:
            self.logs_filter = fltr

    def set_shoot_photo_seq(self, seq):
        self.shoot_photo_seq = seq

    def get_shoot_photo_seq(self):
        return self.shoot_photo_seq

    def set_shoot_video_seq(self, seq):
        self.shoot_video_seq = seq

    def get_shoot_video_seq(self):
        return self.shoot_video_seq

    def set_camera_app_pkg(self, pkg):
        self.camera_app = pkg

    def get_camera_app_pkg(self):
        return self.camera_app

    def do(self, sequence):
        """
        Parses an actions sequence that is passed
        :param sequence: List of actions
        :return:
        """
        self.open_app(self.camera_app)

        for action in sequence:
            act_id = action[0]
            act_data = action[1]
            act_type = act_data[2]
            act_value = act_data[1]
            print(f"Performing {act_id}")
            if act_type == 'tap':
                self.input_tap(act_value)
            if act_type == 'delay':
                print(f"Sleeping {act_value}")
                time.sleep(int(act_value))
            time.sleep(self.actions_time_gap)

    def take_photo(self):
        print("Current mode: ", self.current_camera_app_mode)
        if self.current_camera_app_mode != 'photo':
            self.do(self.goto_photo_seq)
            self.current_camera_app_mode = 'photo'
        self.do(self.shoot_photo_seq)

    def start_video(self):
        print("Current mode: ", self.current_camera_app_mode)
        if self.current_camera_app_mode != 'video':
            self.do(self.goto_video_seq)
            self.current_camera_app_mode = 'video'
            self.is_recording_video = True
        self.do(self.start_video_seq)

    def stop_video(self):
        if self.is_recording_video:
            self.do(self.stop_video_seq)

    def print_attributes(self):
        # For debugging
        print("Object properties:\n")
        print(f"Friendly Name: {self.friendly_name}")
        print(f"Serial: {self.device_serial}")
        print(f"Cam app: {self.camera_app}")
        print(f"Logs: enabled ({self.logs_enabled}), filter ({self.logs_filter})")
        print(f"shoot_photo_seq: {self.shoot_photo_seq}")
        print(f"start_video_seq: {self.start_video_seq}")
        print(f"stop_video_seq: {self.stop_video_seq}")
        print(f"goto_photo_seq: {self.goto_photo_seq}")
        print(f"goto_video_seq: {self.goto_video_seq}")
        print(f"actions_time_gap: {self.actions_time_gap}")
        print(f"settings xml file location: {self.device_xml}")
