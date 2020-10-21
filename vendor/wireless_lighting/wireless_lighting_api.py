from vendor.wireless_lighting.DRL_Dual_INCA_Controller import *
from collections import OrderedDict

from contextlib import redirect_stdout, contextmanager, redirect_stderr
import io
import sys
import threading


def suppress_stdout(func):
    def wrapper(*a, **ka):
        with open(os.devnull, 'w') as devnull:
            with redirect_stdout(devnull):
                func(*a, **ka)
    return wrapper

class HiddenPrints:
    def __enter__(self):
        self._original_stdout = sys.stdout
        sys.stdout = open(os.devnull, 'w')

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout.close()
        sys.stdout = self._original_stdout

class IQL_Dual_WiFi_Wireless_Lighting_API:

    def __str__(self):
        return 'IQL_Dual_WiFi_Wireless_Lighting_API()'

    def __init__(self):
        self.sources = OrderedDict({
            'D65': LightSource('D65', 'D65', 'front', ['G0', 0, 1], [0], [1, 8]),
            'D75': LightSource('D75', 'D75', 'front', [2, 3, 4], [1], [1, 8]),
            'TL84': LightSource('TL84', 'TL84', 'front', [5, 6, 7], [2], [1, 8]),
            'INCA': LightSource('INCA', 'INC A', 'front', [8,9,10,11,12,13,14,15], [3])
        })

        self.cbox_right = ControlBox(lamp_ip='10.66.66.40', dimmer_ip='10.66.66.50', sources=self.sources)
        self.cbox_left = ControlBox(lamp_ip='10.66.66.41', dimmer_ip='10.66.66.51', sources=self.sources)

    def connect(self):
        # with open('lights_output.txt', 'w') as f:
        #     with redirect_stdout(f):
        thread = threading.Thread(target=self.connect, args=(), daemon=True)
        thread.start()

    def _connect(self):
        self.cbox_right.connect()
        self.cbox_left.connect()


if __name__ == "__main__":
    api = IQL_Dual_WiFi_Wireless_Lighting_API()
    print(api)
    api.connect()
    print(api.cbox_left.get_connection_status())