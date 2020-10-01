import os
import time

import PySimpleGUI as sg

import src.constants as constants
from src.app.AutomatedCase import AutomatedCase


def place(elem):
    """
    Places element provided into a Column element so that its placement in the layout is retained.
    :param elem: the element to put into the layout
    :return: A column element containing the provided element
    """
    return sg.Column([[elem]], pad=(0, 0))


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
                    size=(18, 1))
        ],
    ]

    case_frame_layout = [[
        sg.Radio('Photos', "MODE", default=True, key='mode_photos', enable_events=True),
        sg.Radio('Videos', "MODE", key='mode_videos', enable_events=True),
        sg.Radio('Both', "MODE", key='mode_both', enable_events=True, size=(8, 1)),
        sg.Spin([i for i in range(5, 60)], initial_value=10, key='duration_spinner', disabled=True),
        sg.Text('Video Duration (secs)')
    ],
    ]

    post_case_frame_layout = [
        [
            sg.Checkbox('Pull files from device', default=False, size=(16, 1), key='pull_files', enable_events=True),
            sg.Checkbox('and delete them', default=True, size=(12, 1), key='clear_files', disabled=True)
        ],
        [
            sg.Text('Save Location:', size=(11, 1)),
            sg.InputText(size=(36, 1), key='save_location', disabled=True, enable_events=True),
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

        [sg.Button('Run', key='capture_case_btn', size=(54, 2))],

        [sg.Multiline(key='-OUT-', size=(59, 10), autoscroll=True)],
        [sg.ProgressBar(max_value=100, orientation='h', size=(35, 5), key='progressbar', visible=False)],
        [
            place(sg.Text('0', key='progress_value', size=(3, 1), visible=False)),
            place(sg.Text('%', key='progress_value_symbol', pad=(0, 0), visible=False))
        ]
    ]

    window = sg.Window('Automated Photo/Video Testing', layout,
                       icon=os.path.join(constants.ROOT_DIR, 'images', 'automated-video-testing-header-icon.ico'))

    automation_is_running = False
    auto_cases_event = "-AUTO-CASES-THREAD-"

    # Event Loop to process "events" and get the "values" of the inputs
    while True:
        event, values = window.read()

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
            window['capture_case_btn'].Update(disabled=(values['save_location'] == ''))

        if values['pull_files']:
            if values['save_location'] == '':
                print("Save Location must be set!")
                continue

        if event == "capture_case_btn":
            if not automation_is_running:
                window['capture_case_btn'].Update(disabled=True)
                cases = AutomatedCase(attached_devices, devices_obj,
                                      selected_lights_model, values['selected_lights_seq'], selected_luxmeter_model,
                                      values['pull_files'], values['save_location'],
                                      values['mode_photos'] or values['mode_both'],
                                      values['mode_videos'] or values['mode_both'], values['duration_spinner'],
                                      window, '-OUT-', auto_cases_event,
                                      specific_device=None if values['use_all_devices_bool'] else values['selected_device'])
                cases.execute()
            else:
                sg.cprint("Finishing up and stopping cases creation!", window=window, key='-OUT-', colors='white on grey')
                cases.stop_signal = True
                automation_is_running = False
                window['capture_case_btn'].Update('Run')

        if event == auto_cases_event:
            if values[auto_cases_event]['error']:
                window['capture_case_btn'].Update('Run', disabled=False)

            if values[auto_cases_event]['progress'] > 0 and not values[auto_cases_event]['error']:
                automation_is_running = True
                window['capture_case_btn'].Update('Stop', disabled=False)

                window['progressbar'].Update(visible=True, current_count=values[auto_cases_event]['progress'])
                window['progress_value'].Update(str(values[auto_cases_event]['progress']), visible=True)
                window['progress_value_symbol'].Update(visible=True)

            if values[auto_cases_event] == 100:
                sg.Popup('Cases done!')

    window.close()
