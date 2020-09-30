# Uses https://github.com/Swind/pure-python-adb
import subprocess
import os
import threading
import time

from ppadb.client import Client as AdbPy
import src.constants as constants


def compare_lists(list1, list2):
    return [str(s) for s in (set(list1) ^ set(list2))]


class AdbClient:
    """
    AdbClient class takes care of starting ADB, keeping connected devices list and etc.
    """
    def __init__(self, gui_window, gui_event):
        self.gui_window = gui_window
        self.gui_event = gui_event

        print("Starting the ADB Server...")
        try:
            self.adb = subprocess.Popen([constants.ADB, 'start-server'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
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
        self.connected_devices = []

    # ----- Main Stuff -----
    def _watchdog(self):
        time.sleep(1)  # Let's give the GUI time to load
        while True:
            devices_list = self.list_devices()
            attached_devices_list = self.get_attached_devices()

            if len(devices_list) > len(self.connected_devices):  # If New devices found
                for count, diff_device in enumerate(compare_lists(self.connected_devices, devices_list)):
                    self.gui_window.write_event_value(
                        self.gui_event,
                        {
                            'action': 'connected',
                            'serial': diff_device,
                            'type': 'android',
                            'error': False,
                        }
                    )
            elif len(devices_list) < len(self.connected_devices):  # If a device has disconnected
                for count, diff_device in enumerate(compare_lists(self.connected_devices, devices_list)):
                    self.gui_window.write_event_value(
                        self.gui_event,
                        {
                            'action': 'disconnected',
                            'serial': diff_device,
                            'type': 'android',
                            'error': False,
                        }
                    )

            self.connected_devices = devices_list

    def watchdog(self):
        threading.Thread(target=self._watchdog, args=(), daemon=True).start()

    # ----- Getters -----
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

    # ----- Methods -----
    def kill_adb(self):
        """
        Kill opened adb process
        :return:None
        """
        self.adb.terminate()

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
        device_obj.set_led_color('FFFFFF', 'RGB1', 'global_rgb')  # Poly
        device_obj.kill_scrcpy()

        # Finally detach device
        try:
            self.attached_devices.remove(device_serial)
        except ValueError:
            print("Not found in attached devices list")
            print(self.attached_devices)
