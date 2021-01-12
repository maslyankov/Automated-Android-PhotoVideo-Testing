# Uses https://github.com/Swind/pure-python-adb
import subprocess
import threading
import time

from ppadb.client import Client as AdbPy

from src import constants
from src.logs import logger
from src.code.devices.ADBDevice import ADBDevice
from src.code.utils.utils import compare_lists


class AdbClient:
    """
    AdbClient class takes care of starting ADB, keeping connected devices list and etc.
    """

    def __init__(self, gui_window, gui_event):
        self.gui_window = gui_window
        self.gui_event = gui_event

        logger.info("Starting the ADB Server...")
        try:
            self.adb = subprocess.Popen(
                [constants.ADB, 'start-server'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)
            self.adb.stdin.close()
            stdout, stderr = self.adb.communicate()
            if stdout:
                logger.warn("ADB Start Output: " + stdout.decode())  # Debugging
            if stderr:
                logger.error("ADB Start Error: " + stderr.decode())  # Debugging
            self.adb.wait()
        except FileNotFoundError:
            logger.critical("Fatal error: adb not found!")
            return

        self.client = AdbPy(host="127.0.0.1", port=5037)

        self.watchdog_thread = None

        self.connected_devices = []  # to store connected devices
        self.attached_devices = []  # to store attached devices - devices that are connected and we are attached to
        self.devices_obj = {}  # to store attached devices' objects

        self.anticipate_root = False

    # ----- Main Stuff -----
    def _watchdog(self):
        time.sleep(1)  # Let's give the GUI time to load
        while True:
            if self.anticipate_root:
                time.sleep(2)
                self.anticipate_root = False
            try:
                devices_list = self.list_devices()
            except ConnectionResetError:
                logger.error('ADB Server connection lost.')

            if len(devices_list) > len(self.connected_devices):  # If New devices found
                for count, diff_device in enumerate(compare_lists(self.connected_devices, devices_list)):
                    try:
                        self.gui_window.write_event_value(
                            self.gui_event,
                            {
                                'action': 'connected',
                                'serial': diff_device,
                                'type': 'android',
                                'error': False,
                            }
                        )
                    except RuntimeError:
                        logger.warn('Device not ready!')
            elif len(devices_list) < len(self.connected_devices):  # If a device has disconnected
                for count, diff_device in enumerate(compare_lists(self.connected_devices, devices_list)):
                    try:
                        self.gui_window.write_event_value(
                            self.gui_event,
                            {
                                'action': 'disconnected',
                                'serial': diff_device,
                                'type': 'android',
                                'error': False,
                            }
                        )
                    except RuntimeError:
                        logger.warn('Device not ready!')

            self.connected_devices = devices_list

    def watchdog(self):
        self.watchdog_thread = threading.Thread(target=self._watchdog, args=(), daemon=True)
        self.watchdog_thread.name = 'ADBDevices-Watchdog'
        self.watchdog_thread.start()

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

    def attach_device(self, device_serial):
        """
        Add device to attached devices
        :param device_serial: Device serial
        :param device_obj: Device object
        :return: None
        """
        self.devices_obj[device_serial] = ADBDevice(self, device_serial)  # Assign device to object
        self.attached_devices.append(device_serial)

        self.devices_obj[device_serial].set_led_color('0FFF00', 'RGB1', 'global_rgb')  # Poly

    def detach_device(self, device_serial):
        """
        Remove device from attached devices
        :param device_serial: Device serial
        :param device_obj: Device object
        :return: None
        """
        print('Detaching device ', device_serial)
        self.devices_obj[device_serial].kill_scrcpy()

        self.devices_obj[device_serial].set_led_color('FFFFFF', 'RGB1', 'global_rgb')  # Poly

        # Finally detach device
        try:
            self.attached_devices.remove(device_serial)
            del self.devices_obj[device_serial]
        except ValueError:
            logger.warn("Not found in attached devices list")
            print(self.attached_devices)