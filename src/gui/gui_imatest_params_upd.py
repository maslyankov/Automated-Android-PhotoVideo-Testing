import os
import PySimpleGUI as sg

from src import constants
from src.code.reports.ImatestAnalysis import ImatestAnalysis

def gui_imatest_params_upd():
    test_modules_list = list(constants.IMATEST_PARALLEL_TEST_TYPES.keys())
    general_info = [
        [
            sg.Radio('Run Imatest Tests', 'update_type', key='imatest_tests_bool', enable_events=True),
            sg.Radio('From results JSON file', 'update_type', key='import_json_bool', default=True, enable_events=True)
        ],
        [
            sg.Combo(test_modules_list, default_value=test_modules_list[0], key='chosen_module', size=(33, 1), pad=(34, 14))
        ]
    ]

    results_json_frame = [
        [
            sg.Input(key='import_json', size=(35, 1)),
            sg.FileBrowse(file_types=(('JSON Results','*.json'),))
        ]
    ]

    layout = [
        [
            sg.Text('Update Imatest parameters'),
        ],
        [sg.Frame("General", general_info, font='Any 12')],
        [sg.Frame("JSON Result File", results_json_frame, font='Any 12')],
        [sg.Button('Update', key='update_params_btn')]
    ]

    # Create the Window
    window = sg.Window('Update Imatest Params', layout,
                       icon=os.path.join(constants.ROOT_DIR, 'images', 'automated-video-testing-header-icon.ico'))

    while True:
        event, values = window.read()

        if event == sg.WIN_CLOSED or event == 'Close':  # if user closes window or clicks cancel
            break

        window['chosen_module'].Update(visible=values['import_json_bool'])

        if (event == 'update_params_btn' and values['imatest_tests_bool']) and sg.popup_yes_no('Are you sure you want to refetch params from Imatest?\n'
                           'This will do actual tests and parse their results,\n'
                           'so keep in mind it takes some time.') == 'Yes':
            sg.popup_auto_close("Loading... Please wait.", non_blocking=True, no_titlebar=True)
            # Parse to file (Update file)
            ImatestAnalysis.update_imatest_params()
        elif event == 'update_params_btn' and values['import_json_bool']:
            if values['import_json'] == '' or not values['import_json'].endswith('.json'):
                sg.popup_ok('You must choose a JSON file!')
            else:
                ImatestAnalysis.update_imatest_params(json_file=values['import_json'], test_type=values['chosen_module'])
                sg.popup_auto_close('Done!', no_titlebar=True)

    window.close()
