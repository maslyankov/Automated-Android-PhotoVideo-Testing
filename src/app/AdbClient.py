# Uses https://github.com/Swind/pure-python-adb
import subprocess
import os
from ppadb.client import Client as AdbPy

ROOT_DIR = os.path.abspath(os.curdir + "/../")  # This is Project Root
ADB = os.path.join(ROOT_DIR, 'vendor', 'scrcpy-win64-v1.16', 'adb.exe')


class AdbClient:
    """
    AdbClient class takes care of starting ADB, keeping connected devices list and etc.
    """
    def __init__(self):
        print("Starting the ADB Server...")
        try:
            self.adb = subprocess.Popen([ADB, 'start-server'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = self.adb.communicate()
            if stdout:
                print("ADB Start Output: " + stdout.decode())  # Debugging
            if stderr:
                print("ADB Start Error: " + stderr.decode())  # Debugging
            self.adb.wait()
        except FileNotFoundError:
            print("Fatal error: adb not found!")
            return

        self.client = AdbPy(host="127.0.0.1", port=5037)
        self.attached_devices = []  # Store attached devices - devices that are connected and we are attached to

    def kill_adb(self):
        """
        Kill opened adb process
        :return:None
        """
        self.adb.terminate()

    def list_devices(self):
        """
        Get a list of devices from adb server
        :return:List
        """
        devices = []
        for d in self.client.devices():
            devices.append(d.serial)
        return devices  # Return list of devices's serials

    def get_attached_devices(self):
        """
        Get a list of attached devices
        :return:List
        """
        return self.attached_devices

    def attach_device(self, device_serial, device_obj):
        """
        Add device to attached devices
        :param device_serial: Device serial
        :param device_obj: Device object
        :return: None
        """
        device_obj.set_led_color('0FFF00', 'RGB1', 'global_rgb')  # Poly
        self.attached_devices.append(device_serial)

    def detach_device(self, device_serial, device_obj):
        """
        Remove device from attached devices
        :param device_serial: Device serial
        :param device_obj: Device object
        :return: None
        """
        device_obj.set_led_color('FFA600', 'RGB1', 'global_rgb')  # Poly
        try:
            self.attached_devices.remove(device_serial)
        except ValueError:
            print("Not found in attached devices list")
            print(self.attached_devices)
