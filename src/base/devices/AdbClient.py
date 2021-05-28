# Uses https://github.com/Swind/pure-python-adb
from subprocess import PIPE, STDOUT, Popen
from time import sleep, time
from threading import Thread

from ppadb.client import Client as AdbPy

from src import constants
from src.logs import logger
from src.base.devices.ADBDevice import ADBDevice
from src.base.utils.utils import compare_lists


class AdbClient:
    """
    AdbClient class takes care of starting ADB, keeping connected devices list and etc.
    """

    def __init__(self, gui_window, gui_event):
        self.gui_window = gui_window
        self.gui_event = gui_event
        self.gui_is_ready = False

        logger.info("Starting the ADB Server...")
        try:
            self.adb = Popen(
                [constants.ADB, 'start-server'],
                stdin=PIPE,
                stdout=PIPE,
                stderr=PIPE)
            self.adb.stdin.close()
            stdout, stderr = self.adb.communicate()
            if stdout:
                logger.warn("ADB Start Output: " + stdout.decode())  # Debugging
            if stderr:
                logger.error("ADB Start Error: " + stderr.decode())  # Debugging
            self.adb.wait()
        except FileNotFoundError:
            logger.critical("Fatal error: adb not found!")
            logger.info(f"Adb is set to: {constants.ADB}")
            exit(1)

        self.client = AdbPy(host="127.0.0.1", port=5037)

        self.watchdog_thread = None

        self.connected_devices = []  # to store connected devices
        self.attached_devices = []  # to store attached devices - devices that are connected and we are attached to
        self.devices_obj = {}  # to store attached devices' objects

        self.anticipate_root = False

    # ----- Main Stuff -----
    def _watchdog(self):
        counter = 0
        timing_dict = dict()

        while True:
            if self.gui_is_ready:  # Give time for the GUI to load
                sleep(1)
                break

        try:
            self.watchdog_p = Popen(
                [constants.ADB, "track-devices"], creationflags=constants.CREATE_NO_WINDOW,
                stdin=PIPE, stdout=PIPE, stderr=STDOUT)
        except ConnectionResetError:
            logger.error('ADB Server connection lost.')

        for line in self.watchdog_p.stdout:
            logger.debug(f"ADB Watchdog got: {line}")

            data = line.decode("utf-8").split('\t')

            # if self.anticipate_root:
            #     counter = 2
            #     self.anticipate_root = False

            if (int(data[0][2]) == 1):
                try:
                    status = int(data[0][:4], 2)
                except ValueError:
                    status = int(data[0][3]) - 4
                serial = data[0][4:]
            elif (int(data[0][6]) == 1):
                try:
                    status = int(data[0][:8], 2)
                except ValueError:
                    status = int(data[0][7]) - 4
                serial = data[0][8:]
            else:
                logger.error("Status code for device could not be detected!")
                logger.debug(f"We got line: {line}; data: {data}")
                continue

            time_now = time()
            if serial in timing_dict:
                timing_dict[serial]['last_time'] = timing_dict[serial]['time']
                timing_dict[serial]['last_action'] = timing_dict[serial]['action']
                timing_dict[serial]['time_diff'] = time_now - timing_dict[serial]['last_time']
            else:
                timing_dict[serial] = dict()

            timing_dict[serial]['time'] = time_now
            timing_dict[serial]['action'] = status

            if "last_action" in timing_dict[serial] and timing_dict[serial]['action'] == timing_dict[serial]['last_action']:
                # print("\nSkipping this action as it seems duplicated!")
                continue
            else:
                if self.anticipate_root:
                    logger.debug(f"Not minding the device updates as we are anticipating root!")
                    # counter -= 1
                elif status == 2:  # If a device has connected
                    try:
                        logger.debug(f"Device {serial} connected")
                        self.gui_window.write_event_value(
                            self.gui_event,
                            {
                                'action': 'connected',
                                'serial': serial,
                                'type': 'android',
                                'error': False,
                            }
                        )
                        try:
                            self.connected_devices.append(serial)
                        except ValueError:
                            logger.error("Tried to add device from conn devices, but it seems to be already listed there!")
                    except RuntimeError:
                        logger.warn('Device not ready!')
                elif status == 3:  # If a device has disconnected
                    try:
                        logger.debug(f"Device {data[0]} disconnected")
                        self.gui_window.write_event_value(
                            self.gui_event,
                            {
                                'action': 'disconnected',
                                'serial': serial,
                                'type': 'android',
                                'error': False,
                            }
                        )
                        try:
                            self.connected_devices.remove(serial)
                        except ValueError:
                            logger.error("Tried to remove device from conn devices, but it does not seem to be listed there!")
                    except RuntimeError:
                        logger.warn('Device not ready!')
                else:
                    logger.error(f"Unknown device status received! -> {status}")

        logger.debug("ADB Watchdog exiting...")

    def watchdog(self):
        self.watchdog_thread = Thread(target=self._watchdog, args=(), daemon=True)
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

    def detach_device(self, device_serial, spurious_bool = False):
        """
        Remove device from attached devices
        :param device_serial: Device serial
        :param device_obj: Device object
        :return: None
        """

        # Finally detach device
        if self.attached_devices:
            try:
                logger.info(f'Detaching device {device_serial}')
                self.devices_obj[device_serial].kill_scrcpy()

                if not spurious_bool:
                    # Optional stuff
                    self.devices_obj[device_serial].set_led_color('FFFFFF', 'RGB1', 'global_rgb')  # Poly

                self.attached_devices.remove(device_serial)
                del self.devices_obj[device_serial]
            except ValueError as e:
                logger.warn(f"Not found in attached devices list")
                logger.exception(e)
                logger.debug(self.attached_devices)
            except KeyError as e:
                logger.warn(f"Not found in attached devices list")
                logger.exception(e)
                logger.debug(self.attached_devices)

    def __del__(self):
        self.watchdog_p.kill()
