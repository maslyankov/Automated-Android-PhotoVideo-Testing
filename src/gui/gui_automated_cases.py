import os
import time

import PySimpleGUI as sg

import src.constants as constants
from src.app.AutomatedCase import AutomatedCase


def gui_automated_cases(attached_devices, devices_obj, selected_lights_model, selected_luxmeter_model):  # TODO
    select_device_frame = [
        [sg.Checkbox(text='Use all attached devices',
                     default=True,
                     key='use_all_devices_bool',
                     enable_events=True)],
        [
            sg.Combo(attached_devices, size=(20, 20),
                     key='selected_device',
                     default_value=attached_devices[0],
                     enable_events=True,
                     disabled=True),
            sg.Text(text=devices_obj[attached_devices[0]].friendly_name,
                    key='device-friendly',
                    font="Any 18",
                    auto_size_text=True)
        ],
    ]

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
            sg.InputText(size=(35, 1), key='save_location', disabled=True, enable_events=True),
            sg.FolderBrowse(key='save_location_browse_btn')
        ],
    ]

    lights_frame_layout = [
        [
            sg.Text('Sequence to use:'),
            sg.Combo(values=['demo'], key='selected_lights_seq', default_value='demo', size=(30, 1))
        ]
    ]

    layout = [
        [sg.Frame('Select Device', select_device_frame, font='Any 12', title_color='white')],
        [sg.Frame('Test Case', case_frame_layout, font='Any 12', title_color='white')],
        [sg.Frame('After Case', post_case_frame_layout, font='Any 12', title_color='white')],
        [sg.Frame('Lights', lights_frame_layout, font='Any 12', title_color='white')],
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
            window['device-friendly'].Update(devices_obj[values['selected_device']].friendly_name)

        if event == 'use_all_devices_bool':
            window['selected_device'].Update(disabled=values['use_all_devices_bool'])

        if event == 'save_location':
            if values["pull_files"]:
                window['capture_case_btn'].Update(disabled=False)

        if event == "pull_files":
            window['clear_files'].Update(disabled=not values['pull_files'])
            window['save_location'].Update(disabled=not values['pull_files'])
            window['save_location_browse_btn'].Update(disabled=not values['pull_files'])
            if values['save_location'] == '':
                window['capture_case_btn'].Update(disabled=True)
            elif values['save_location'] != '':
                window['capture_case_btn'].Update(disabled=False)

        if event == "capture_case_btn":
            # Photos Mode
            # if values['mode_photos'] or values['mode_both']:
            #     # shoot_photo(device_obj, values['logs_bool'], values['logs_filter'],
            #     #           "{}/logfile.txt".format(values['save_location']))
            #     device_obj[values['selected_device']].take_photo()
            #
            # # Videos Mode
            # if values['mode_videos'] or values['mode_both']:
            #     # shoot_video(device_obj, values['duration_spinner'], values['logs_bool'], values['logs_filter'],
            #     #            "{}/logfile.txt".format(values['save_location']))
            #     device_obj[values['selected_device']].start_video()
            #     print(f"Video started! Duration is: {values['duration_spinner']}")
            #     time.sleep(values['duration_spinner'])
            #     device_obj[values['selected_device']].stop_video()
            sg.Popup('Starting Cases!', non_blocking=True, auto_close=True, auto_close_duration=5)

            cases = AutomatedCase(attached_devices, devices_obj, selected_lights_model, values['selected_lights_seq'], selected_luxmeter_model)
            cases.execute()

            sg.Popup('Cases done!')

            if values['pull_files']:
                if values['save_location']:
                    # pull_camera_files(device_obj, values['save_location'], values['clear_files'])
                    pass
                else:
                    print("Save Location must be set!")

    window.close()
