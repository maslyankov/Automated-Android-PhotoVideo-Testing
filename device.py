import subprocess
import time
import xml.etree.ElementTree as ET
import re

from coords import *

SNAP_CAM = "org.codeaurora.snapcam"  # TODO Make this an option in app settings


class Device:
    def __init__(self, adb_client, device_serial):
        print("Connecting to device...")

        self.d = adb_client.device(device_serial)
        self.device_serial = device_serial

        print("Device Serial: ", device_serial)

    def exec_shell(self, cmd):
        return self.d.shell(cmd)

    def input_tap(self, *coords): # Send tap events
        self.d.shell("input tap {} {}".format(coords[0][0], coords[0][1]))

    def start_video(self):
        self.input_tap(shoot_video())

    def stop_video(self):
        self.input_tap(stop_video())

    def take_photo(self):
        self.input_tap(shoot_photo())

    def get_current_app(self):
        return self.d.shell("dumpsys window windows | grep -E 'mFocusedApp'| cut -d / -f 1 | cut -d ' ' -f 7").rstrip()

    def open_snap_cam(self): # Todo Make this with an argument for app package
        if self.get_current_app() != SNAP_CAM:
            print("Opening Snap Cam...")
            self.d.shell("monkey -p '{}' -v 1".format(SNAP_CAM))
        else:
            print("Snap Cam was already opened! Continuing...")

    def push_file(self, src, dst):
        self.d.push(src, dst)

    def pull_file(self, src, dst):
        self.d.pull(src, dst)

    def remount(self):
        print("Remount device serial: " + self.device_serial)
        remount = subprocess.Popen(['adb.exe', '-s', self.device_serial, 'remount'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = remount.communicate()
        print("Remonut Errors: ".format(stderr.decode()))
        print("Remonut Output: ".format(stdout.decode()))
        remount.terminate()

    def reboot(self):
        self.d.shell("reboot")

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

    def identify(self):
        for i in range(0, 4):
            self.d.shell('input keyevent 26')
            #time.sleep(0.2)

    def dump_window_elements(self):
        # "adb -s {} shell uiautomator dump && adb -s {} pull /sdcard/window_dump.xml {}
        self.d.shell('uiautomator dump')
        self.d.pull('/sdcard/window_dump.xml', './XML/{}_{}.xml'.format(self.device_serial, self.get_current_app()))
        print('Dumped window elements for current app')

    def get_clickable_window_elements(self):
        self.dump_window_elements()

        print('Parsing xml...')

        xml_tree = ET.parse("./XML/{}_{}.xml".format(self.device_serial, self.get_current_app()))
        xml_root = xml_tree.getroot()

        for element in xml_root.iter("node"):
            # this will print a list of the contents of the tag
            elem_res_id = element.attrib['resource-id']
            elem_desc = element.attrib['content-desc']
            elem_bounds = re.findall(r'\[([^]]*)\]', element.attrib['bounds'])[0].split(',')

            if (elem_res_id or elem_desc) and int(elem_bounds[0]) > 0:
                print("Elem {} ({}) - {}".format(elem_desc, elem_res_id, elem_bounds))

