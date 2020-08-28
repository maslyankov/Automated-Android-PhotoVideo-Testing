# Uses https://github.com/Swind/pure-python-adb
import subprocess
from ppadb.client import Client as AdbPy


class AdbClient:
    def __init__(self):
        print("Starting the ADB Server...")
        try:
            self.adb = subprocess.Popen(['adb.exe', 'root'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
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

    def kill_adb(self):
        self.adb.terminate()

    def list_devices(self):
        devices = []
        for d in self.client.devices():
            devices.append(d.serial)
        return devices  # Return list of devices's serials