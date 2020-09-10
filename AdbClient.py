# Uses https://github.com/Swind/pure-python-adb
import subprocess
from ppadb.client import Client as AdbPy

ADB = "./scrcpy-win64-v1.16/adb.exe"

class AdbClient:
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
        self.adb.terminate()

    def list_devices(self):
        devices = []
        for d in self.client.devices():
            devices.append(d.serial)
        return devices  # Return list of devices's serials

    def get_attached_devices(self):
        return self.attached_devices

    def attach_device(self, device_serial, device_obj):
        device_obj.set_led_color(100, 'RGB1', 'global_rgb')  # Poly
        self.attached_devices.append(device_serial)

    def detach_device(self, device_serial, device_obj):
        device_obj.set_led_color(10, 'RGB1', 'global_rgb')  # Poly
        try:
            self.attached_devices.remove(device_serial)
        except ValueError:
            print("Not found in attached devices list")
            print(self.attached_devices)
