import os
import PySimpleGUI as sg

from src import constants
from src.logs import logger


def gui_push_file(attached_devices, device_obj):
    file_destinations = [
        'sdcard/DCIM/',
        'vendor/lib/',
        'vendor/lib/camera/',
        'vendor/lib64/',
        'vendor/lib64/camera/'
    ]

    layout = [
        [
            sg.Text('Device: ', size=(9, 1)),
            sg.Combo(attached_devices, size=(20, 20),
                     enable_events=True, key='selected_device',
                     default_value=attached_devices[0]),
            sg.Text(text=device_obj[attached_devices[0]].friendly_name,
                    key='device-friendly',
                    size=(13, 1),
                    font="Any 18")
        ],
        [
            sg.Text('Destination: ', size=(9, 1)),
            sg.Combo(file_destinations, size=(20, 20), key='dest_folder', default_value=file_destinations[0])
        ],
        [
            sg.Text('File/s:', size=(9, 1)),
            sg.InputText(size=(40, 1), key='source_file', enable_events=True),
            sg.FilesBrowse()
        ],
        [
            sg.Button('Disable Verity', key='disable_verity_btn', size=(10, 2)),
            sg.Button('Push File', size=(10, 2),
                   key='push_file_btn', disabled=True)]
    ]

    # Create the Window
    window = sg.Window('Push file/s', layout,
                       icon=os.path.join(constants.ROOT_DIR, 'images', 'automated-video-testing-header-icon.ico'))

    while True:
        event, values = window.read()

        if event == sg.WIN_CLOSED or event == 'Close':  # if user closes window or clicks cancel
            break

        logger.debug(f'vals: {values}')  # Debugging
        logger.debug(f'event: {event}')  # Debugging

        if event == 'selected_device':
            window['device-friendly'].Update(device_obj[values['selected_device']].friendly_name)

        if event == 'source_file':
            window['push_file_btn'].Update(disabled=False)

        if event == 'disable_verity_btn':
            curr_device = device_obj[values['selected_device']]

            curr_device.disable_verity()
            curr_device.detach_device()

            logger.info(f'Verity Disabled!\nDevice reattachment is necessary.')
            sg.popup_ok(f'Verity Disabled!\nYou might need to reattach to device.')

        if event == 'push_file_btn':
            curr_device = device_obj[values['selected_device']]
            files_dest = values['dest_folder']

            logger.debug(values['source_file'].split(';'))

            logger.info("Remounting Device...")
            curr_device.remount()
            logger.info("Pushing new file to device...")

            curr_device.push_files(values['source_file'].split(';'), files_dest)

            logger.info('Files pushed!')
            sg.popup_ok('Files pushed!')

    window.close()
