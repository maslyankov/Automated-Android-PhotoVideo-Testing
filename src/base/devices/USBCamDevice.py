from src.base.devices.Device import Device


class USBCamDevice(Device):
    def __init__(self, serial, port):
        super().__init__(serial)

        self.port = port

    def take_photo(self):
        pass

    def start_video(self):
        pass

    def stop_video(self):
        pass