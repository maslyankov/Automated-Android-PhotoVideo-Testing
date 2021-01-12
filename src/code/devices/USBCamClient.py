import threading
import time

# from pygrabber.dshow_graph import FilterGraph

from src.code.utils.utils import compare_lists
from src.code.devices.USBCamDevice import USBCamDevice
from src.logs import logger


def list_ports():
    # graph = FilterGraph()
    # cams_enumerated = enumerate(graph.get_input_devices())
    out_dict = {}

    # print('Names list: ', cams_enumerated)
    # for cam_id, cam_name in cams_enumerated:
    #     print(f"Camera {cam_id}: {cam_name}")
    #     out_dict[cam_name] = cam_id

    return out_dict


class USBCamClient:
    def __init__(self, gui_window, gui_event):
        self.gui_window = gui_window
        self.gui_event = gui_event

        self.watchdog_thread = None

        self.connected_devices = []  # to store connected devices

        self.attached_devices = []  # to store attached devices - devices that are connected and we are attached to
        self.devices_obj = {}  # to store attached devices' objects

    # ----- Main Stuff -----
    def _watchdog(self):
        time.sleep(1)  # Let's give the GUI time to load
        while True:
            ports_dict = list_ports()
            devices_list = list(ports_dict.values())

            if len(devices_list) > len(self.connected_devices):  # If New devices found
                for count, diff_device in enumerate(compare_lists(self.connected_devices, devices_list)):
                    friendly_name = list(ports_dict.keys)[diff_device]
                    serial = friendly_name.replace(' ', '').lower()

                    self.gui_window.write_event_value(
                        self.gui_event,
                        {
                            'action': 'connected',
                            'serial': serial,
                            'port': diff_device,
                            'type': 'usb_cam',
                            'friendly_name': friendly_name,
                            'error': False,
                        }
                    )
            elif len(devices_list) < len(self.connected_devices):  # If a device has disconnected
                for count, diff_device in enumerate(compare_lists(self.connected_devices, devices_list)):
                    friendly_name = list(ports_dict.keys)[diff_device]
                    serial = friendly_name.replace(' ', '').lower()

                    self.gui_window.write_event_value(
                        self.gui_event,
                        {
                            'action': 'disconnected',
                            'serial': serial,
                            'port': diff_device,
                            'type': 'usb_cam',
                            'friendly_name': friendly_name,
                            'error': False,
                        }
                    )

            self.connected_devices = devices_list

    def watchdog(self):
        self.watchdog_thread = threading.Thread(target=self._watchdog, args=(), daemon=True)
        self.watchdog_thread.name = 'USBCameras-Watchdog'

        logger.info(f"Starting {self.watchdog_thread.name} Thread")
        self.watchdog_thread.start()

    def attach_device(self, device_serial, port):
        """
        Add device to attached devices
        :param port:
        :param device_serial: Device serial
        :param device_obj: Device object
        :return: None
        """
        logger.info(f"Attaching device {device_serial} at {port}")

        self.devices_obj[device_serial] = USBCamDevice(device_serial, port)  # Assign device to object
        self.attached_devices.append(device_serial)

    def detach_device(self, device_serial):
        """
        Remove device from attached devices
        :param device_serial: Device serial
        :param device_obj: Device object
        :return: None
        """
        logger.info(f'Detaching device {device_serial}')

        # Finally detach device
        try:
            self.attached_devices.remove(device_serial)
            del self.devices_obj[device_serial]
        except ValueError:
            logger.error(f"Not found in attached devices list\n{self.attached_devices}")
