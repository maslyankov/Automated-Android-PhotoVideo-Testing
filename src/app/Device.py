import subprocess
import time
import re
import os
import xml.etree.cElementTree as ET
from natsort import natsorted

from src.temp.coords import *

SNAP_CAM = "org.codeaurora.snapcam"  # TODO Make this an option in app settings

# DIRECTORIES
ROOT_DIR = os.path.abspath(os.curdir + "/../")  # This is Project Root
ADB = os.path.join(ROOT_DIR, 'vendor', 'scrcpy-win64-v1.16', 'adb.exe')
SCRCPY = os.path.join(ROOT_DIR, 'vendor', 'scrcpy-win64-v1.16', 'scrcpy.exe')


# CLASS Device
class Device:
    def __init__(self, adb, device_serial):
        print("Attaching to device...")

        self.adb = adb
        self.adb_client = adb.client
        self.d = self.adb_client.device(device_serial)  # Create device client object

        self.device_serial = device_serial  # Assign device serial as received in arguments
        self.friendly_name = self.get_device_model()

        self.root()  # Make sure we are using root for device

        # Add device to attached devices list
        adb.attach_device(device_serial, self)
        print("Conn devs: ", adb.attached_devices)  # Debugging
        print("Device Serial: ", device_serial)  # Debugging
        print("Resolution: ", self.get_screen_resolution())  # Debugging

    def root(self):
        print("Rooting device " + self.device_serial)
        root = subprocess.Popen([ADB, '-s', self.device_serial, 'root'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
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
        print("Remount device serial: " + self.device_serial)
        remount = subprocess.Popen([ADB, '-s', self.device_serial, 'remount'], stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        stdout, stderr = remount.communicate()
        if stderr:
            print("Remonut Errors: ".format(stderr.decode()))
        if stdout:
            print("Remonut Output: ".format(stdout.decode()))
        remount.terminate()

    def exec_shell(self, cmd):
        return self.d.shell(cmd)

    def input_tap(self, *coords):  # Send tap events
        self.d.shell("input tap {} {}".format(coords[0][0], coords[0][1]))

    def reboot(self):
        self.d.shell("reboot")  # TODO Remove device from connected_devices list after reboot
        # self.adb.detach_device(self.device_serial, self)

    def get_current_app(self):  # Returns currently opened app package and its current activity
        return self.d.shell("dumpsys window windows | grep -E 'mFocusedApp'").split(' ')[6].split('/')

    def get_device_model(self):
        return self.d.shell("getprop ro.product.model").rstrip()

    def get_device_name(self):
        return self.d.shell("getprop ro.product.name").rstrip()

    def get_installed_packages(self):
        return self.d.shell("cmd package list packages -e | sort").replace('package:', '').splitlines()

    def open_app(self, package):
        if self.get_current_app() != package:
            print("Opening {}...".format(package))
            self.d.shell("monkey -p '{}' -v 1".format(package))
        else:
            print("{} was already opened! Continuing...".format(package))

    def push_file(self, src, dst):
        self.d.push(src, dst)

    def pull_file(self, src, dst):
        self.d.pull(src, dst)

    def get_camera_files_list(self):
        try:
            files_list = self.d.shell("ls -1 sdcard/DCIM/Camera").splitlines()
            if files_list[0] == 'ls: sdcard/DCIM/Camera: No such file or directory':  # TODO Fix this shit
                return
            else:
                return files_list
        except:
            print("sdcard/DCIM/Camera not found")

    def clear_camera_folder(self):
        self.d.shell("rm -rf sdcard/DCIM/Camera/*")
        print("Deleting files from device!")

    def has_screen(self):  # TODO Make this return a valid boolean (now it sometimes works, sometimes doesn't)
        before = self.d.shell("dumpsys deviceidle | grep mScreenOn").split('=')[1].strip()
        self.d.shell('input keyevent 26')
        time.sleep(0.5)
        after = self.d.shell("dumpsys deviceidle | grep mScreenOn").split('=')[1].strip()

        if before == after:
            print("Device has no integrated screen!")

        self.d.shell('input keyevent 26')

    def get_screen_resolution(self):
        return self.d.shell('dumpsys window | grep "mUnrestricted"').rstrip().split(' ')[1].split('x')

    def get_device_leds(self):
        return natsorted(self.d.shell("ls /sys/class/leds/").strip().replace('\n', '').replace('  ', ' ').split(' '))

    def set_led_color(self, value, led, target):
        try:
            self.d.shell('echo {} > /sys/class/leds/{}/{}'.format(value, led, target))
        except RuntimeError:
            print("Device was disconnected before we could detach it properly.. :(")

    def open_device_ctrl(self):
        print("Opening scrcpy for device ", self.device_serial)
        scrcpy = subprocess.Popen([SCRCPY, '--serial', self.device_serial], stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE)
        # stdout, stderr = scrcpy.communicate()
        # if stderr:
        #    print("Scrspy Errors: \n{}\n".format(stderr.decode()))
        # if stdout:
        #    print("Scrspy Output: \n{}\n".format(stdout.decode()))

    def identify(self):
        leds = self.get_device_leds()
        print(leds)  # Debugging

        for k in range(1, 5):  # Blink Leds and screen
            if k != 1:
                time.sleep(0.5)
            self.d.shell('echo 0 > /sys/class/leds/{}/global_onoff'.format(leds[0]))
            time.sleep(0.3)
            self.d.shell('echo 1 > /sys/class/leds/{}/global_onoff'.format(leds[0]))

            self.d.shell('input keyevent 26')  # Event Power Button

        for led in leds:
            self.d.shell('echo 0 > /sys/class/leds/{}/color_setting'.format(led))

        print('Finished identifying!')

    def dump_window_elements(self):
        source = self.d.shell('uiautomator dump').split(': ')[1].rstrip()
        current_app = self.get_current_app()
        if source == "null root node returned by UiTestAutomationBridge.":
            print("UIAutomator error! :( Try dumping UI elements again. (It looks like a known error)")
            return

        self.d.pull(
            source,
            os.path.join(ROOT_DIR, 'XML', '{}_{}_{}.xml'.format(self.device_serial, current_app[0], current_app[1]))
        )
        print('Dumped window elements for current app.')

    def get_clickable_window_elements(self):
        print('Parsing xml...')
        current_app = self.get_current_app()
        print("Serial {} , app: {}".format(self.device_serial, current_app))
        file = os.path.join(ROOT_DIR, 'XML', '{}_{}_{}.xml'.format(self.device_serial, current_app[0], current_app[1]))
        try:
            xml_tree = ET.parse(file)
        except FileNotFoundError:
            self.dump_window_elements()
            xml_tree = ET.parse(file)
        except ET.ParseError as error:
            print("XML Parse Error: ", error)

        xml_root = xml_tree.getroot()
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

    # Will be changed [START]
    def open_snap_cam(self):  # Todo Make this with an argument for app package
        if self.get_current_app()[0] != SNAP_CAM:
            print("Opening Snap Cam...")
            self.d.shell("monkey -p '{}' -v 1".format(SNAP_CAM))
        else:
            print("Snap Cam was already opened! Continuing...")

    def start_video(self):
        self.input_tap(shoot_video())

    def stop_video(self):
        self.input_tap(stop_video())

    def take_photo(self):
        self.input_tap(shoot_photo())
    # Will be changed [END]
