import os

import PySimpleGUI as sg

import src.constants as constants
from src.app.AutomatedCase import AutomatedCase

from src.gui.gui_automated_cases_lights_xml_gui import lights_xml_gui
from src.gui.utils_gui import place
import threading

def configurable_tab_logic(window, values, event,
                           cases, auto_cases_event):
    window['duration_spinner'].Update(disabled=values['mode_photos'])
    if event == 'save_location':
        if values["pull_files"]:
            window['capture_cases_btn'].Update(disabled=False)

    if event == "pull_files":
        # window['clear_files'].Update(disabled=not values['pull_files'])  # Does not affect anything yet
        window['save_location'].Update(disabled=not values['pull_files'])
        window['save_location_browse_btn'].Update(disabled=not values['pull_files'])
        window['capture_cases_btn'].Update(disabled=(values['save_location'] == ''))

    if event == 'manage_lights_btn':
        lights_xml_gui(values['selected_lights_seq'])

    if event == "capture_cases_btn":
        if values['pull_files'] and values['save_location'] == '':
            print("Save Location must be set!")
        else:
            try:
                if not cases.is_running:
                    window['capture_cases_btn'].Update(disabled=True)
                    try:
                        cases.execute(values['selected_lights_seq'],
                                  values['pull_files'], values['save_location'],
                                  values['mode_photos'] or values['mode_both'],
                                  values['mode_videos'] or values['mode_both'], video_duration=values['duration_spinner'],
                                  specific_device=None if values['use_all_devices_bool'] else values['selected_device'])
                    except ValueError as e:
                        cases.stop_signal = True
                        sg.popup_error(e)
                else:
                    sg.cprint("Finishing up and stopping cases creation!", window=window, key='-OUT-',
                              colors='white on grey')
                    cases.stop_signal = True
                    window['capture_cases_btn'].Update(disabled=True)
            except AttributeError:
                pass

    if event == auto_cases_event:
        if values[auto_cases_event]['error']:
            window['capture_cases_btn'].Update('Run', disabled=False)

        if values[auto_cases_event]['progress'] > 0 and not values[auto_cases_event]['error']:
            window['capture_cases_btn'].Update('Stop', disabled=False)

        if values[auto_cases_event]['progress'] == 100:
            sg.Popup('Cases done!')

    try:
        if cases.is_running:
            window['capture_cases_btn'].Update('Stop')
        else:
            window['capture_cases_btn'].Update('Run')
    except AttributeError:
        pass


def template_tab_logic(window, values, event,
                       cases, auto_cases_event):
    window['generate_reports_pdf_bool'].Update(disabled=not values['generate_reports_bool'])

    if event == 'run_template_automation_btn':
        cases.execute_req_template(values['template_location'], values['save_location_output'],
                                   values['generate_reports_bool'], values['generate_reports_pdf_bool'],
                                   specific_device=None if values['use_all_devices_bool'] else values['selected_device'])

    if event == auto_cases_event:
        if values[auto_cases_event]['error']:
            window['run_template_automation_btn'].Update(disabled=False)

        if values[auto_cases_event]['progress'] > 0 and not values[auto_cases_event]['error']:
            window['run_template_automation_btn'].Update('Stop', disabled=False)

        if values[auto_cases_event]['current_action'] == 'finished':
            sg.Popup('Cases done!')

    try:
        if cases.is_running:
            window['run_template_automation_btn'].Update('Stop')
        else:
            window['run_template_automation_btn'].Update('Run')
    except AttributeError:
        pass


def gui_automated_cases(adb, selected_lights_model, selected_luxmeter_model):
    attached_devices = adb.attached_devices
    devices_obj = adb.devices_obj

    # COMMON ELEMENTS
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

    # CONFIGURABLE TAB
    case_frame_layout = [[
        sg.Radio('Photos', "MODE", default=True, key='mode_photos', enable_events=True),
        sg.Radio('Videos', "MODE", key='mode_videos', enable_events=True),
        sg.Radio('Both', "MODE", key='mode_both', enable_events=True, size=(8, 1)),
        sg.Spin([i for i in range(5, 60)], initial_value=10, key='duration_spinner', disabled=True),
        sg.Text('Video Duration (secs)')
    ], ]

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
            sg.Combo(values=['demo'], key='selected_lights_seq', default_value='demo', size=(31, 1)),
            sg.B('Manage', key='manage_lights_btn')
        ]
    ]

    diff_tuning_layout = []

    configurable_tab = [
        [sg.Frame('Test Case', case_frame_layout, font='Any 12', title_color='white')],
        [sg.Frame('After Case', post_case_frame_layout, font='Any 12', title_color='white')],
        [sg.Frame('Lights', lights_frame_layout, font='Any 12', title_color='white')],
        [sg.Frame('Queue sequences with different tunings', diff_tuning_layout, font='Any 12', title_color='white')],

        [sg.Button('Run', key='capture_cases_btn', size=(54, 2))]
    ]

    # TEMPLATE TAB
    template_frame = [
        [
            sg.Text('Use:'),
            sg.InputText(size=(36, 1), key='template_location', disabled=True, enable_events=True),
            sg.FilesBrowse(
                key='template_browse_btn',
                file_types=(
                    ('Microsoft Excel', '*.xls *.xlsx *.xlsm *.xltx *.xltm'),
                )
            )
        ]
    ]

    checklist_frame = [[
        sg.Checkbox('Generate Report', default=True, key='generate_reports_bool', enable_events=True),
        sg.Checkbox('Generate PDF', default=True, key='generate_reports_pdf_bool'),
    ]]

    destination_frame = [[
        sg.Text('Save Location:', size=(11, 1)),
        sg.InputText(size=(36, 1), key='save_location_output', disabled=True, enable_events=True),
        sg.FolderBrowse(key='save_location_output_browse_btn')
    ]]

    template_tab = [
        [sg.Frame('Template', template_frame, font='Any 12', title_color='white')],
        [sg.Frame('Checklist', checklist_frame, font='Any 12', title_color='white')],
        [sg.Frame('Save to...', destination_frame, font='Any 12', title_color='white')],
        [sg.Button('DO THE MAGIC', key='run_template_automation_btn', size=(54, 2))]
    ]

    layout = [
        [sg.Frame('Select Device', select_device_frame, font='Any 12', title_color='white')],
        [sg.TabGroup([[
            sg.Tab('Configurable', configurable_tab, key='configurable_cases_tab'),
            sg.Tab('Template Testing', template_tab, key='template_cases_tab')
        ]], key='auto_cases_tabs_group', enable_events=True)],

        [sg.Multiline(key='-OUT-', size=(59, 10), autoscroll=True)],
        [sg.ProgressBar(max_value=100, orientation='h', size=(35, 5), key='progressbar', visible=False)],
        [
            place(sg.Text('0', key='progress_value', size=(3, 1), visible=False)),
            place(sg.Text('%', key='progress_value_symbol', pad=(0, 0), visible=False)),

            place(sg.Text('', key='progress_curr_module', pad=(5, 0), visible=False))
        ]
    ]

    window = sg.Window('Automated Photo/Video Testing', layout,
                       icon=os.path.join(constants.ROOT_DIR, 'images', 'automated-video-testing-header-icon.ico'))

    auto_cases_event = "-AUTO-CASES-THREAD-"

    main_gui_window = adb.gui_window
    adb.gui_window = window
    devices_watchdog_event = '-DEVICES-WATCHDOG-'

    cases = None
    # Event Loop to process "events" and get the "values" of the inputs
    while True:
        event, values = window.read()

        # print('values: ', values)  # debugging

        if event == sg.WIN_CLOSED or event == 'Close':  # if user closes window or clicks cancel
            break

        if event == devices_watchdog_event:
            print(values[devices_watchdog_event])

        if event == 'selected_device':
            window['device-friendly'].Update(devices_obj[values['selected_device']].friendly_name)

        if event == 'use_all_devices_bool':
            window['selected_device'].Update(disabled=values['use_all_devices_bool'])

        if event == auto_cases_event:
            if values[auto_cases_event]['progress'] > 0 and not values[auto_cases_event]['error']:
                window['progressbar'].Update(visible=True, current_count=values[auto_cases_event]['progress'])
                window['progress_value'].Update(str(values[auto_cases_event]['progress']), visible=True)
                window['progress_value_symbol'].Update(visible=True)
                window['progress_curr_module'].Update(str(values[auto_cases_event]['current_action']), visible=True)

        if values['auto_cases_tabs_group'] == 'configurable_cases_tab':
            print('tab is at configurable cases')
            configurable_tab_logic(
                window, values, event,
                cases, auto_cases_event
            )

        if values['auto_cases_tabs_group'] == 'template_cases_tab':
            print('tab is at template cases')
            template_tab_logic(
                window, values, event,
                cases, auto_cases_event
            )


        if cases is None:
            cases = AutomatedCase(adb, selected_lights_model, selected_luxmeter_model,
                                  window, '-OUT-', auto_cases_event)
            cases.start()
            #cases.prep()
            #cases.run_prereq()


    adb.gui_window = main_gui_window
    window.close()
