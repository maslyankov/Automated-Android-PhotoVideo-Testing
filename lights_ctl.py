from wireless_lighting_api import IQL_Dual_WiFi_Wireless_Lighting_API
import time

# Instance API object
api = IQL_Dual_WiFi_Wireless_Lighting_API()

# Connect to Light box
api.connect()

while True:
    # Turn on D65
    api.cbox_right.set_lamp("D65", 0, 1)
    api.cbox_right.set_lamp("D65", 1, 1)
    api.cbox_right.set_lamp("D65", 2, 1)
    api.cbox_right.set_dimmer("D65", 100)
    time.sleep(5)

    # Turn off D65
    api.cbox_right.set_lamp("D65", 0, 0)
    api.cbox_right.set_lamp("D65", 1, 0)
    api.cbox_right.set_lamp("D65", 2, 0)
    time.sleep(1)

    # Turn on D75
    api.cbox_right.set_lamp("D75", 0, 1)
    api.cbox_right.set_lamp("D75", 1, 1)
    api.cbox_right.set_lamp("D75", 2, 1)
    api.cbox_right.set_dimmer("D75", 100)
    time.sleep(5)

    # Turn off D75
    api.cbox_right.set_lamp("D75", 0, 0)
    api.cbox_right.set_lamp("D75", 1, 0)
    api.cbox_right.set_lamp("D75", 2, 0)
    time.sleep(1)

    # Turn on TL84
    api.cbox_right.set_lamp("TL84", 0, 1)
    api.cbox_right.set_lamp("TL84", 1, 1)
    api.cbox_right.set_lamp("TL84", 2, 1)
    api.cbox_right.set_dimmer("TL84", 100)
    time.sleep(5)

    # Turn off TL84
    api.cbox_right.set_lamp("TL84", 0, 0)
    api.cbox_right.set_lamp("TL84", 1, 0)
    api.cbox_right.set_lamp("TL84", 2, 0)
    time.sleep(1)

    # Turn INCA ON
    api.cbox_right.set_lamp("INCA", 0, 1)
    api.cbox_right.set_lamp("INCA", 1, 1)
    api.cbox_right.set_lamp("INCA", 2, 1)
    api.cbox_right.set_lamp("INCA", 3, 1)
    api.cbox_right.set_lamp("INCA", 4, 1)
    api.cbox_right.set_lamp("INCA", 5, 1)
    api.cbox_right.set_dimmer("INCA", 100)
    time.sleep(4)

    # Turn INCA Off
    api.cbox_right.set_lamp("INCA", 0, 0)
    api.cbox_right.set_lamp("INCA", 1, 0)
    api.cbox_right.set_lamp("INCA", 2, 0)
    api.cbox_right.set_lamp("INCA", 3, 0)
    api.cbox_right.set_lamp("INCA", 4, 0)
    api.cbox_right.set_lamp("INCA", 5, 0)
    time.sleep(1)
