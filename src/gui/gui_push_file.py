import os
import PySimpleGUI as sg

from src import constants
from src.logs import logger
from src.gui.utils_gui import collapse


def gui_push_file(device_obj, attached_devices=None, specific_device=None):
    if specific_device:
        device_obj[specific_device].load_settings_file()
        persist_setting = device_obj[specific_device].get_persist_setting('last_push_file_save_dir')
    else:
        device_obj[specific_device].load_settings_file()
        persist_setting = device_obj[attached_devices[0]].get_persist_setting('last_push_file_save_dir')

    file_destinations = [
        'vendor/lib/',
        'vendor/lib/camera/',
        'vendor/lib64/',
        'vendor/lib64/camera/',
        'vendor/etc/chicamera/',
        'sdcard/DCIM/'
    ]

    select_device_layout = [
        [
            sg.Text('Device: ', size=(9, 1)),
            sg.Combo(attached_devices if attached_devices else [], size=(20, 20),
                     enable_events=True, key='selected_device',
                     default_value=attached_devices[0] if attached_devices else ""),
            sg.Text(text=device_obj[attached_devices[0]].friendly_name if attached_devices else "",
                    key='device-friendly',
                    size=(13, 1),
                    font="Any 18")
        ]
    ]

    layout = [
        [collapse(select_device_layout, 'select_device_layout', not bool(specific_device))],
        [
            sg.Text('Destination: ', size=(9, 1)),
            sg.Combo(file_destinations, size=(20, 20),
                     key='dest_folder',
                     default_value=persist_setting if persist_setting else file_destinations[0])
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

        curr_device = device_obj[values['selected_device']] if not specific_device else device_obj[specific_device]

        if attached_devices and event == 'selected_device':
            window['device-friendly'].Update(curr_device.friendly_name)

            persist_setting = curr_device.get_persist_setting('last_push_file_save_dir')
            window['dest_folder'].Update(persist_setting)

        if event == 'source_file':
            window['push_file_btn'].Update(disabled=False)

        if event == 'disable_verity_btn':
            curr_device.disable_verity()
            curr_device.detach_device()

            logger.info(f'Verity Disabled!\nDevice reattachment is necessary.')
            sg.popup_ok(f'Verity Disabled!\nYou might need to reattach to device.')

        if event == 'push_file_btn':
            files_dest = values['dest_folder']

            logger.debug(values['source_file'].split(';'))

            logger.info("Remounting Device...")
            curr_device.remount()
            logger.info("Pushing new file to device...")

            curr_device.push_files(values['source_file'].split(';'), files_dest)

            curr_device.set_persist_setting("last_push_file_save_dir", files_dest)
            curr_device.save_settings()

            logger.info('Files pushed!')
            sg.popup_ok('Files pushed!')

    window.close()
