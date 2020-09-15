import os
import time
from vendor.wireless_lighting.wireless_lighting_api import IQL_Dual_WiFi_Wireless_Lighting_API

ROOT_DIR = os.path.abspath(os.curdir + "/../")  # This is Project Root
LIGHTS_MODELS = {
    'SpectriWave': 0,
    'lightStudio': 1
}


class LightsCtrl:
    def __init__(self, model):
        self.current_color_temp = None
        self.current_brightness = None

        print('Selected light model: ', LIGHTS_MODELS.get(model, "Invalid light model"))
        self.lights_model = LIGHTS_MODELS[model]

        if self.lights_model == LIGHTS_MODELS['SpectriWave']:
            self.available_lights = ['D65', 'D75', 'TL84', 'INCA']
            # Instance API object
            self.api = IQL_Dual_WiFi_Wireless_Lighting_API()

            # Connect to Light box
            self.api.connect()
            print("This is the output", self.api.cbox_left.get_connection_status())

            pass

    def status(self):
        if self.lights_model == LIGHTS_MODELS['SpectriWave']:
            status = self.api.cbox_left.get_connection_status(), self.api.cbox_right.get_connection_status()

        print(status)
        return status




    def turn_on(self, color_temp, selected_target_light='all'):
        # TODO add check if color_temp is in self.available_lights
        if self.lights_model == LIGHTS_MODELS['SpectriWave']:
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

        if self.lights_model == LIGHTS_MODELS['SpectriWave']:
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

        if self.lights_model == LIGHTS_MODELS['SpectriWave']:
            self.api.cbox_right.set_dimmer(self.current_color_temp, target_brightness)

        self.current_brightness = target_brightness
        print(f"Set [{self.current_color_temp}] to {target_brightness}")

    def set_color_temp(self, color_temp):
        self.current_color_temp = color_temp

    def disconnect(self):
        print("Disconnecting from lights...")
        for light_color in self.available_lights:
            self.turn_off(light_color)

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
