import subprocess
import time
import re
import os
import sys
import xml.etree.cElementTree as ET
from natsort import natsorted

import src.constants as constants
from src.temp.coords import *


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

        # Object Parameters #
        # Info
        self.device_serial = device_serial  # Assign device serial as received in arguments
        self.friendly_name = self.get_device_model()

        # Settings
        self.camera_app = None
        self.shoot_photo_seq = []
        self.shoot_video_seq = []
        self.goto_photo_seq = []
        self.goto_video_seq = []
        self.actions_time_gap = 1

        self.root()  # Make sure we are using root for device

        # Add device to attached devices list
        adb.attach_device(device_serial, self)

        # Persistence
        self.device_xml = os.path.join(constants.ROOT_DIR, 'settings', f'{device_serial}.xml')
        # self.save_settings()

        print("Conn devs: ", adb.attached_devices)  # Debugging
        print("Device Serial: ", device_serial)  # Debugging

    def root(self):
        """
        Root the device
        :return:None
        """
        print("Rooting device " + self.device_serial)
        root = subprocess.Popen([constants.ADB, '-s', self.device_serial, 'root'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
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
        # print("X: ", coords[0][0], "Y: ", coords[0][1])  # Debugging
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
        return self.d.shell("dumpsys window windows | grep -E 'mFocusedApp'").split(' ')[6].split('/')

    def get_device_model(self):
        """
        Get the device model
        :return: String of device model
        """
        return self.d.shell("getprop ro.product.model").rstrip()

    def get_device_name(self):
        """
        Get the device name
        :return: String of device name
        """
        return self.d.shell("getprop ro.product.name").rstrip()

    def get_installed_packages(self):
        """
        Get the packages (apps) installed on device
        :return:List of strings, each being an app package on the device
        """
        return self.d.shell("cmd package list packages -e | sort").replace('package:', '').splitlines()

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
        try:
            files_list = self.d.shell("ls -1 sdcard/DCIM/Camera").splitlines()
            if files_list[0] == 'ls: sdcard/DCIM/Camera: No such file or directory':  # TODO Fix this shit
                return
            else:
                return files_list
        except:
            print("sdcard/DCIM/Camera not found")

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
        scrcpy = subprocess.Popen([constants.SCRCPY, '--serial', self.device_serial], stdout=subprocess.PIPE,
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

        self.d.pull(
            source,
            os.path.join(constants.ROOT_DIR, 'XML', '{}_{}_{}.xml'.format(self.device_serial, current_app[0], current_app[1]))
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
        print("Serial {} , app: {}".format(self.device_serial, current_app))
        file = os.path.join(constants.ROOT_DIR, 'XML', '{}_{}_{}.xml'.format(self.device_serial, current_app[0], current_app[1]))

        if force_dump:
            self.dump_window_elements()

        try:
            xml_tree = ET.parse(file)
        except FileNotFoundError:
            self.dump_window_elements()
            xml_tree = ET.parse(file)
        except ET.ParseError as error:
            print("XML Parse Error: ", error)

        try:
            xml_root = xml_tree.getroot()
        except AttributeError:
            print("XML wasn't opened correctly!")
        elements = {}

        for num, element in enumerate(xml_root.iter("node")):
            elem_res_id = element.attrib['resource-id'].split('/')
            elem_desc = element.attrib['content-desc']
            elem_bounds = re.findall(r'\[([^]]*)\]', element.attrib['bounds'])[0].split(',')

            if (elem_res_id or elem_desc) and int(elem_bounds[0]) > 0:
                elem_bounds[0] = int(elem_bounds[0]) + 1
                elem_bounds[1] = int(elem_bounds[1]) + 1
                if elem_res_id[0] != '':
                    elements[elem_res_id[1]] = elem_desc, elem_bounds
                else:
                    elements[num] = elem_desc, elem_bounds

        return elements

    def save_settings(self):
        root = ET.Element('device')

        # Device info
        info = ET.SubElement(root, 'info')
        root.append(info)

        serial = ET.SubElement(info, "serial")
        serial.text = self.device_serial

        name = ET.SubElement(info, "name")
        name.text = self.get_device_name()

        model = ET.SubElement(info, "model")
        model.text = self.get_device_model()

        friendly = ET.SubElement(info, "friendly_name")
        friendly.text = self.friendly_name

        resolution = ET.SubElement(info, "screen_resolution")
        res_data = self.get_screen_resolution()
        resolution.text = f'{res_data[0]}x{res_data[1]}'

        # Device settings
        settings = ET.SubElement(root, 'settings')
        root.append(settings)

        cam_app = ET.SubElement(settings, "camera_app")
        cam_app.text = self.camera_app

        shoot_photo_seq = ET.SubElement(settings, "shoot_photo_seq")
        for action in self.shoot_photo_seq:
            elem = ET.SubElement(shoot_photo_seq, "action")
            elem_id = ET.SubElement(elem, "id")  # set
            elem_desc = ET.SubElement(elem, "description")  # set
            elem_coordinates = ET.SubElement(elem, "coordinates")

            x = ET.SubElement(elem_coordinates, "x")  # set
            y = ET.SubElement(elem_coordinates, "y")  # set

            # list should be: self.shoot_photo_seq = [['element_id', ['Description', [x, y]]]]            elem_id.text = str(action[0])
            elem_id.text = action[0]
            elem_desc.text = action[1][0]
            x.text = str(action[1][1][0])
            y.text = str(action[1][1][1])

        shoot_video_seq = ET.SubElement(settings, "shoot_video_seq")
        for action in self.shoot_video_seq:
            # set elements
            elem = ET.SubElement(shoot_video_seq, "action")
            elem_id = ET.SubElement(elem, "id")  # set
            elem_desc = ET.SubElement(elem, "description")  # set
            elem_coordinates = ET.SubElement(elem, "coordinates")
            x = ET.SubElement(elem_coordinates, "x")
            y = ET.SubElement(elem_coordinates, "y")

            # Set value
            # list should be: self.shoot_video_seq = [['element_id', ['Description', [x, y]]]]
            elem_id.text = str(action[0])
            elem_desc.text = str(action[1][0])
            x.text = str(action[1][1][0])
            y.text = str(action[1][1][1])

        actions_time_gap = ET.SubElement(settings, "actions_time_gap")
        actions_time_gap.text = str(self.actions_time_gap)

        # Clear file
        print('Clearing file..')

        old_root = ET.parse(self.device_xml).getroot()
        print(old_root)
        old_root.clear()

        try:
            old_root = ET.parse(self.device_xml).getroot()
        except ET.ParseError:
            print("File is possibly empty.. Not clearing then.")
        else:
            old_root.clear()


        # Save to file
        tree = ET.ElementTree(root)
        print('Writing settings to file...')
        #tree.write(str(self.device_xml), encoding='utf-8', xml_declaration=True)

    def set_shoot_photo_seq(self, seq):
        self.shoot_photo_seq = seq

    def get_shoot_photo_seq(self):
        return self.shoot_photo_seq

    def set_shoot_video_seq(self, seq):
        self.shoot_video_seq = seq

    def get_shoot_video_seq(self):
        return self.shoot_video_seq

        # Will be changed [START]
    def start_video(self):
        self.input_tap(shoot_video())

    def stop_video(self):
        self.input_tap(stop_video())

    def take_photo(self):
        self.input_tap(shoot_photo())
    # Will be changed [END]
