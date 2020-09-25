import os
import time
from vendor.wireless_lighting.wireless_lighting_api import IQL_Dual_WiFi_Wireless_Lighting_API

import src.constants as constants


class LightsCtrl:
    def __init__(self, model):
        self.current_color_temp = None
        self.current_brightness = 1

        print('Selected light model: ', constants.LIGHTS_MODELS.get(model, "Invalid light model"))
        self.lights_model = constants.LIGHTS_MODELS[model]

        if self.lights_model == constants.LIGHTS_MODELS['SpectriWave']:
            self.available_lights = ['D65', 'D75', 'TL84', 'INCA']
            # Instance API object
            self.api = IQL_Dual_WiFi_Wireless_Lighting_API()

            # Connect to Light box
            self.api.connect()
        else:
            self.available_lights = []

    def status(self):
        if self.lights_model == constants.LIGHTS_MODELS['SpectriWave']:
            return self.api.cbox_left.get_connection_status(), \
                   self.api.cbox_right.get_connection_status()

    def turn_on(self, color_temp, selected_target_light='all'):
        # TODO add check if color_temp is in self.available_lights
        if self.lights_model == constants.LIGHTS_MODELS['SpectriWave']:
            if color_temp != 'INCA' and selected_target_light != 'all' and int(selected_target_light) > 2:
                selected_target_light = 'all'
            num_lights_of_type = 3 if color_temp != 'INCA' else 6
            if selected_target_light == 'all':
                for target_light in range(0, num_lights_of_type):
                    self.api.cbox_right.set_lamp(color_temp, target_light, 1)
            else:
                self.api.cbox_right.set_lamp(color_temp, int(selected_target_light), 1)
                print('I did: ', color_temp, selected_target_light, 1)

        self.current_color_temp = color_temp
        print(f"[{color_temp}] turning on")

    def turn_off(self, color_temp, selected_target_light='all'):
        # TODO add check if color_temp is in self.available_lights

        if self.lights_model == constants.LIGHTS_MODELS['SpectriWave']:
            if color_temp != 'INCA' and selected_target_light != 'all' and int(selected_target_light) > 2:
                selected_target_light = 'all'
            num_lights_of_type = 3 if color_temp != 'INCA' else 6
            if selected_target_light == 'all':
                for target_light in range(0, num_lights_of_type):
                    self.api.cbox_right.set_lamp(color_temp, target_light, 0)
            else:
                self.api.cbox_right.set_lamp(color_temp, int(selected_target_light), 0)
                print('I did: ', color_temp, selected_target_light, 0)

        self.current_color_temp = color_temp
        print(f"[{color_temp}] turning on")

    def set_brightness(self, target_brightness):
        if self.current_color_temp is None:
            print("Color temp not set.")
            return

        if target_brightness > 100 or target_brightness < 0:
            print("Target brightness invalid.")
            return

        if self.lights_model == constants.LIGHTS_MODELS['SpectriWave']:
            self.api.cbox_right.set_dimmer(self.current_color_temp, target_brightness)

        self.current_brightness = target_brightness
        print(f"Set [{self.current_color_temp}] to {target_brightness}")

    def set_color_temp(self, color_temp):
        self.current_color_temp = color_temp

    def set_lux(self, luxmeter_obj, target_lux):
        print(f"Setting lux to {target_lux}")
        curr_lux = luxmeter_obj.get_lux()
        threshold = 10  # How much can we vary with lux value
        luxmeter_resp_time = 0.6
        lights_resp_time = 1
        step = 4
        print('\n\n\nBefore diff: ', abs(curr_lux - target_lux), '\n\n\n')

        while abs(curr_lux - target_lux) > threshold:
            print(f"Target lux: {target_lux}, current lux: {curr_lux}")
            if curr_lux > target_lux:  # We need to go down
                self.set_brightness(self.current_brightness - step)
            elif curr_lux < target_lux:  # We need to go up
                self.set_brightness(self.current_brightness + step)
            else:  # If we are at the exact luxes (this seems almost impossible, I think)
                break

            # Wait for lights to adjust
            time.sleep(lights_resp_time)
            curr_lux = luxmeter_obj.get_lux()  # Update lux measurement

        print(f"[Set Lux] Target LUX was {target_lux}, we got it to {curr_lux}, because the threshold is {threshold}")

    def disconnect(self):
        print("Disconnecting from lights...")
        if self.lights_model == constants.LIGHTS_MODELS['SpectriWave']:
            for light_color in self.available_lights:
                print(f"Turning off {light_color}")
                self.turn_off(light_color)
            time.sleep(1)  # Added delay, because the API is slow
            self.api.cbox_left.disconnect()
            self.api.cbox_right.disconnect()

    def make_a_party(self):
        # Test D65
        self.turn_on("D65")
        self.set_brightness(100)

        time.sleep(5)

        self.set_brightness(50)

        time.sleep(3)

        self.turn_off("D65")

        # Test D75
        self.turn_on("D75")
        self.set_brightness(100)

        time.sleep(5)

        self.set_brightness(50)

        time.sleep(3)

        self.turn_off("D75")

        # Test TL84
        self.turn_on("TL84")
        self.set_brightness(100)

        time.sleep(5)

        self.set_brightness(50)

        time.sleep(3)

        self.turn_off("TL84")

        # Test INCA
        self.turn_on("INCA")
        self.set_brightness(100)

        time.sleep(5)

        self.set_brightness(50)

        time.sleep(3)

        self.turn_off("INCA")
