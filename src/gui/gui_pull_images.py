import os
import PySimpleGUI as sg

from src import constants
from src.logs import logger


def gui_pull_images(attached_devices, device_obj):
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
        [
            sg.T("Save destination:"),
            sg.I(key='save_dest'),
            sg.FolderBrowse()
        ],
        [sg.Button('Pull', size=(10, 2),
                   key='pull_btn', disabled=False)]
    ]

    # Create the Window
    window = sg.Window('Reboot Device', layout,
                       icon=os.path.join(constants.ROOT_DIR, 'images', 'automated-video-testing-header-icon.ico'))

    while True:
        event, values = window.read()

        if event == sg.WIN_CLOSED or event == 'Close':  # if user closes window or clicks cancel
            break

        print('vals', values)  # Debugging
        print('event', event)  # Debugging

        if event == 'selected_device':
            window['device-friendly'].Update(device_obj[values['selected_device']].friendly_name)

        if event == 'pull_btn':
            curr_device = device_obj[values['selected_device']]

            logger.info(f"Pulling from device {values['selected_device']}")

            save_dir = values['save_dest']

            if save_dir and os.path.isdir(save_dir):
                device_images_dir = curr_device.images_save_loc
                # files_to_pull = adb_devices[attached_devices_list[0]].get_recursive_files_list(device_images_dir)
                # print(files_to_pull)

                curr_device.pull_files_recurse([device_images_dir], save_dir)

    window.close()
