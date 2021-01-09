import os
import time

import PySimpleGUI as sg

from src import constants
from src.logs import logger


def gui_manual_cases(attached_devices, device_obj):  # TODO
    select_device_frame = [[
        sg.Combo(attached_devices, size=(20, 20),
                 key='selected_device',
                 default_value=attached_devices[0],
                 enable_events=True),
        sg.Text(text=device_obj[attached_devices[0]].friendly_name,
                key='device-friendly',
                font="Any 18",
                auto_size_text=True)
    ],]

    case_frame_layout = [[
        sg.Radio('Photos', "MODE", default=True, key='mode_photos', enable_events=True),
        sg.Radio('Videos', "MODE", key='mode_videos', enable_events=True),
        sg.Radio('Both', "MODE", key='mode_both', enable_events=True),
        sg.Spin([i for i in range(5, 60)], initial_value=10, key='duration_spinner', disabled=True),
        sg.Text('Video Duration (secs)')
    ],
    ]

    post_case_frame_layout = [
        [
            sg.Checkbox('Pull files from device', default=False, size=(16, 1), key='pull_files', enable_events=True),
            sg.Checkbox('and delete them', default=True, size=(12, 1), key='clear_files')
        ],
        [
            sg.Text('Save Location:', size=(11, 1)),
            sg.InputText(size=(35, 1), key='save_location', enable_events=True),
            sg.FolderBrowse(key='save_location_browse_btn')
        ],
    ]

    layout = [
        [sg.Frame('Select Device', select_device_frame, font='Any 12')],
        [sg.Frame('Test Case', case_frame_layout, font='Any 12')],
        [sg.Frame('After Case', post_case_frame_layout, font='Any 12')],
        [sg.Button('Do Case', key='capture_case_btn')]
    ]

    window = sg.Window('Automated Photo/Video Testing', layout,
                       icon=os.path.join(constants.ROOT_DIR, 'images', 'automated-video-testing-header-icon.ico'))

    # Event Loop to process "events" and get the "values" of the inputs
    while True:
        event, values = window.read(timeout=100)

        if event == sg.WIN_CLOSED or event == 'Close':  # if user closes window or clicks cancel
            break

        window['duration_spinner'].Update(disabled=values['mode_photos'])

        if event == 'selected_device':
            window['device-friendly'].Update(device_obj[values['selected_device']].friendly_name)

        if event == 'save_location':
            if values["pull_files"]:
                window['capture_case_btn'].Update(disabled=False)

        if event == "pull_files":
            window['clear_files'].Update(disabled=not values['pull_files'])
            window['save_location'].Update(disabled=not values['pull_files'])
            window['save_location_browse_btn'].Update(disabled=not values['pull_files'])
            if values['save_location'] == '':  # TODO FIX THIS
                window['capture_case_btn'].Update(disabled=True)

        if event == "capture_case_btn":
            # Photos Mode
            if values['mode_photos'] or values['mode_both']:
                # shoot_photo(device_obj, values['logs_bool'], values['logs_filter'],
                #           "{}/logfile.txt".format(values['save_location']))
                device_obj[values['selected_device']].take_photo()

            # Videos Mode
            if values['mode_videos'] or values['mode_both']:
                # shoot_video(device_obj, values['duration_spinner'], values['logs_bool'], values['logs_filter'],
                #            "{}/logfile.txt".format(values['save_location']))
                device_obj[values['selected_device']].start_video()
                logger.info(f"Video started! Duration is: {values['duration_spinner']}")
                time.sleep(values['duration_spinner'])
                device_obj[values['selected_device']].stop_video()

            if values['pull_files']:
                if values['save_location']:
                    # pull_camera_files(device_obj, values['save_location'], values['clear_files'])
                    pass
                else:
                    logger.error("Save Location must be set!")

    window.close()
