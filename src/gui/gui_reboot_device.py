import os
import PySimpleGUI as sg

from src import constants
from src.logs import logger


def gui_reboot_device(attached_devices, device_obj):
    layout = [
        [
            sg.Combo(attached_devices, size=(20, 20),
                     key='selected_device',
                     default_value=attached_devices[0],
                     enable_events=True),
            sg.Text(text=device_obj[attached_devices[0]].friendly_name,
                    key='device-friendly',
                    font="Any 18",
                    size=(13, 1))
        ],
        [sg.Button('Reboot', size=(10, 2),
                   key='reboot_device_btn', disabled=False)]
    ]

    # Create the Window
    window = sg.Window('Reboot Device', layout,
                       icon=os.path.join(constants.ROOT_DIR, 'images', 'automated-video-testing-header-icon.ico'))

    while True:
        event, values = window.read()

        if event == sg.WIN_CLOSED or event == 'Close':  # if user closes window or clicks cancel
            break

        logger.debug('vals', values)  # Debugging
        logger.debug('event', event)  # Debugging

        if event == 'selected_device':
            window['device-friendly'].Update(device_obj[values['selected_device']].friendly_name)

        if event == 'reboot_device_btn':
            curr_device = device_obj[values['selected_device']]

            logger.info(f"Rebooting Device {values['selected_device']}")
            curr_device.reboot()
            sg.popup_auto_close("Reboot successful! Detaching device...")

    window.close()
