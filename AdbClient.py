# Uses https://github.com/Swind/pure-python-adb
import subprocess
from ppadb.client import Client as AdbPy


class AdbClient:
    def __init__(self):
        print("Starting the ADB Server...")
        try:
            self.adb = subprocess.Popen(['adb.exe', 'start-server'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
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
        self.connected_devices = []  # Store connected devices

    def kill_adb(self):
        self.adb.terminate()

    def list_devices(self):
        devices = []
        for d in self.client.devices():
            devices.append(d.serial)
        return devices  # Return list of devices's serials

    def get_connected_devices(self):
        return self.connected_devices

    def connect_device(self, device_serial):
        self.connected_devices.append(device_serial)

    def disconnect_device(self, device_serial, object):
        # object.set_led_color('asd')
        self.connected_devices.remove(device_serial)
