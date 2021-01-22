import time

from src.base.devices.konica.ChromaMeterKonica import ChromaMeterKonica
from src import constants
from src.logs import logger


class Sensor:
    def __init__(self, device):
        if device not in constants.LUXMETERS_MODELS.values():
            logger.critical(f'Invalid sensor device!\n Sensor: {device}')
            raise ValueError(f'Invalid sensor device!\n Sensor: {device}')
        if device == constants.LUXMETERS_MODELS['Konita Minolta CL-200A']:
            # For Konita Minolta CL-200A
            self.sensor_obj = ChromaMeterKonica()
            self.is_alive = self.sensor_obj.is_alive
        if device == constants.LUXMETERS_MODELS['test']:
            # For test luxmeter
            self.fake_lux = 40
            self.is_alive = True

        self.device = device

    def get_lux(self):
        if self.device == constants.LUXMETERS_MODELS['test']:
            time.sleep(1)
            return self.fake_lux

        return self.sensor_obj.get_lux()
