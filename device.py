# Uses https://github.com/Swind/pure-python-adb
import subprocess

from ppadb.client import Client as AdbClient

from pathlib import Path
import io

from coords import *

# SNAP_CAM = "org.codeaurora.snapcam"


class AdbClient:
    def __init__(self):
        print("Starting the ADB Server...")
        try:
            adb = subprocess.Popen(['adb.exe', 'root'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = adb.communicate()
            if stdout:
                print("ADB Start Output: " + stdout.decode())  # Debugging
            if stderr:
                print("ADB Start Error: " + stderr.decode())  # Debugging
            adb.wait()
        except FileNotFoundError:
            print("Fatal error: adb not found!")
            return

        client = AdbClient(host="127.0.0.1", port=5037)

    def list_devices(self):
        devices = []
        for d in self.client.devices():
            devices.append(d.serial)
        return devices  # Return list of devices's serials


class Device:
    def __init__(self, device_serial):
        self.d = adb.device(serial=device_serial)

        print("Connecting to device...")
        print("Device Serial: ", self.d.serial)

        # Argument support list, str
        serial = self.d.shell("getprop ro.serial")

        # show property, also based on d.shell
        print("Device Name: ", self.d.prop.name, "\n")  # output example: surabaya

        self.d.prop.get("ro.product.model")
        self.d.prop.get("ro.product.model", cache=True)  # a little faster, use cache data first

    def input_tap(self, *coords):
        # self.d.shell("input tap {} {}".format(coords[0][0], coords[0][1]))
        self.d.click(coords[0][0], coords[0][1])

    def exec_shell(self, cmd):
        return self.d.shell(cmd)

    def start_video(self):
        self.input_tap(shoot_video())

    def stop_video(self):
        self.input_tap(stop_video())

    def take_photo(self):
        self.input_tap(shoot_photo())

    def get_current_app(self):
        return self.d.shell("dumpsys window windows | grep -E 'mFocusedApp'| cut -d / -f 1 | cut -d ' ' -f 7")

    def open_snap_cam(self):
        if self.get_current_app() != SNAP_CAM:
            print("Opening Snap Cam...")
            self.d.shell("monkey -p '{}' -v 1".format(SNAP_CAM))
        else:
            print("Snap Cam was already opened! Continuing...")

    def push_file(self, src, dst):
        self.d.sync.push(open(src, "rb"), dst) # TODO Fix this

    def pull_file(self, src, dst):
        self.d.sync.pull(src, dst)

    def reboot(self):
        self.exec_shell("reboot")

    def get_camera_files_list(self):
        try:
            files_list = self.exec_shell("ls -1 sdcard/DCIM/Camera").splitlines()
            if files_list[0] == 'ls: sdcard/DCIM/Camera: No such file or directory': # TODO Fix this shit
                return
            else:
                return files_list
        except:
            print("sdcard/DCIM/Camera not found")

    def clear_camera_folder(self):
        self.exec_shell("rm -rf sdcard/DCIM/Camera/*")
        print("Deleting files from device!")
