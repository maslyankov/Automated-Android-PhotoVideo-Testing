import os
import PySimpleGUI as sg

from src import constants
from src.logs import logger
from src.gui.utils_gui import collapse


def gui_screenrec(device_obj, attached_devices=None, specific_device=None):
    if specific_device:
        device_obj[specific_device].load_settings_file()
        persist_setting = device_obj[specific_device].get_persist_setting('last_screenrec_save_dest')
    else:
        device_obj[specific_device].load_settings_file()
        persist_setting = device_obj[attached_devices[0]].get_persist_setting('last_screenrec_save_dest')

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
            sg.Text('Destination:', size=(9, 1)),
            sg.InputText(size=(40, 1), key='dest_folder', enable_events=True,
                         default_text=persist_setting if persist_setting else ""),
            sg.FolderBrowse()
        ],
        [
            sg.T("To end the recording, simply close the screen mirroring window.")
        ],
        [
            sg.Button('Start Recording', size=(15, 2),
                   key='start_rec_btn', disabled=False if persist_setting else True),
            sg.Button('Stop', size=(15, 2),
                      key='stop_rec_btn', disabled=True),
        ]
    ]

    # Create the Window
    window = sg.Window('Screen Recording', layout,
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

        window['start_rec_btn'].Update(disabled=values['dest_folder'] == '')

        if event == 'start_rec_btn' and not values['dest_folder'] == '':

            files_dest = values['dest_folder']

            logger.debug(f"Got dest folder: {files_dest} and device {curr_device.device_serial}")

            curr_device.record_device_ctrl(files_dest)

            curr_device.set_persist_setting("last_screenrec_save_dest", files_dest)
            curr_device.save_settings()

            logger.info('Recording started!')
            sg.popup_auto_close("Recording started!")

            window['stop_rec_btn'].Update(disabled=False)

        if event == 'stop_rec_btn':
            window['stop_rec_btn'].Update(disabled=True)

            curr_device.kill_scrcpy()

    window.close()
