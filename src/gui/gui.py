import os

import PySimpleGUI as sg

from src import constants
from src.logs import logger

from src.base.devices.AdbClient import AdbClient

from src.base.reports.RLReports import generate_rlt_report
from src.base.reports.ObjectiveReports import generate_obj_report

from src.gui.gui_help import gui_help
from src.gui.gui_camxoverride import gui_camxoverride
from src.gui.gui_manual_cases import gui_manual_cases
from src.gui.gui_automated_cases import gui_automated_cases
from src.gui.gui_push_file import gui_push_file
from src.gui.gui_pull_file import gui_android_file_browser
from src.gui.gui_reboot_device import gui_reboot_device
from src.gui.gui_screenrec import gui_screenrec
from src.gui.gui_setup_device import gui_setup_device
from src.gui.gui_test_lights import gui_test_lights
from src.gui.gui_project_req_file import gui_project_req_file
from src.gui.gui_cam_tool import gui_cam_tool
from src.gui.gui_extract_video_frames_tool import gui_extract_video_frames_tool
from src.gui.utils_gui import place, Tabs, collapse, explorer_open_file


def gui():
    # sg.theme('DarkBlack')  # Add a touch of color
    # Set GUI theme
    set_gui_theme()

    devices_frame = []
    for num in range(constants.MAX_DEVICES_AT_ONE_RUN):
        logger.debug(f"Building row {num}")  # Debugging
        devices_frame += [
                             place(sg.Image(filename='', key=f'device_icon.{num}', visible=False)),
                             place(sg.Checkbox('', key=f'device_attached.{num}',
                                               disabled=True,
                                               enable_events=True,
                                               visible=False,
                                               size=(17, 1))),
                             place(sg.InputText(key=f'device_serial.{num}',
                                                size=(15, 1),
                                                readonly=True,
                                                default_text='',
                                                visible=False)),
                             place(sg.InputText(key=f'device_friendly.{num}', enable_events=True, size=(23, 1),
                                                disabled=True,
                                                visible=False)),
                             place(sg.Button('Identify',
                                             key=f'identify_device_btn.{num}',
                                             disabled=True,
                                             enable_events=True,
                                             visible=False)),
                             place(sg.Button('Control',
                                             key=f'ctrl_device_btn.{num}',
                                             disabled=True,
                                             enable_events=True,
                                             visible=False
                                             ))
                         ],

    # noinspection PyTypeChecker
    device_settings_frame_layout = [[
        sg.Button('Edit camxoverridesettings',
                  size=(19, 2),
                  key='camxoverride_btn',
                  disabled=True,
                  tooltip='Edit or view camxoverridesettings of any attached device'),
        sg.Button('Reboot Device',
                  size=(19, 2),
                  key='reboot_device_btn',
                  disabled=True,
                  tooltip='Reboot devices immediately'),
        sg.Button('Setup',
                  size=(19, 2),
                  key='setup_device_btn',
                  disabled=True,
                  tooltip='Setup device settings, calibrate touch events etc.'),
    ],
    ]

    device_tools_layout = [
        [
            sg.Button('Push file/s',
                      size=(12, 3),
                      key='push_file_btn',
                      disabled=True),
            sg.Button('Pull file/s',
                      size=(12, 3),
                      key='pull_file_btn',
                      disabled=True),
            sg.Button('Record Screen',
                      size=(12, 3),
                      key='record_screen_btn',
                      disabled=True)
        ]
    ]

    lights_frame_layout = [[
        sg.OptionMenu(
            values=list(constants.LIGHTS_MODELS.keys()),
            key="selected_lights_model",
            default_value='test' if constants.DEBUG_MODE else list(constants.LIGHTS_MODELS.keys())[0],
            size=(22, 1)
        ),
        sg.OptionMenu(
            values=list(constants.LUXMETERS_MODELS.keys()),
            key="selected_luxmeter_model",
            default_value='test' if constants.DEBUG_MODE else list(constants.LUXMETERS_MODELS.keys())[0],
            size=(22, 1)
        ),
        sg.Button(
            'Test Lights',
            size=(11, 3),
            key='test_lights_btn',
            disabled=False
        ),
    ],
    ]

    # Tab 2
    global templ_data
    objective_frame_layout = [
        [
            sg.T('Project Requirements: ', size=(18, 1)),
            sg.Input(key='obj_report_projreq_field', readonly=True, size=(36, 1)),
            sg.Button(button_text='Open', key='obj_report_projreq_btn', size=(8, 1))
        ],
        [
            sg.T('Images dir:', size=(18, 1)),
            sg.Input(key='obj_report_output', readonly=True, size=(36, 1), enable_events=True),
            sg.FolderBrowse(size=(8, 1), key='obj_report_output_browse')
        ],
        [sg.Button("Generate", key='obj_report_build_btn', size=(20, 1), disabled=True)]
    ]

    ### Real Life Reports

    #         "image_path": r"C:\Users\mms00519\Downloads\Indoor_cases",
    #         "thumbnail_path": r"C:\Users\mms00519\Downloads\Indoor_cases\Thumbnail",
    #         "presentation_name": "RLT_presentation",
    #         "attribute_on": 1,

    # Collapsables
    global opened_conf_main, opened_conf_summ_params, opened_conf_summ_items, opened_conf_attribute
    opened_conf_main, opened_conf_summ_params, opened_conf_summ_items, opened_conf_attribute = False, False, False, False

    #         "avg_luma": True,
    #         "contrast": True,
    #         "black_level": True,
    #         "white_level": True,
    #         "over_exposed": True,
    #         "under_exposed": True,
    #         "dynamic_range": False,
    #         "peak_saturation1": False,
    #         "peak_hue1": False,
    #         "peak_saturation2": False,
    #         "peak_hue2": False,
    #         "sharpness": True,
    #         "ISO": True,
    #         "ET": True
    conf_main_layout = [
        [
            sg.Checkbox(text='Avg Luma', default=True, key='conf_main_avg_luma_bool', pad=((0, 20), 0)),
            sg.Checkbox(text='Contrast', default=True, key='conf_main_contrast_bool', pad=((0, 20), 0)),
            sg.Checkbox(text='Black level', default=True, key='conf_main_black_level_bool', pad=((0, 20), 0)),
            sg.Checkbox(text='White level', default=True, key='conf_main_white_level_bool', pad=((0, 20), 0)),
            sg.Checkbox(text='Over Exposed', default=True, key='conf_main_over_exposed_bool', pad=((0, 20), 0)),
        ],
        [
            sg.Checkbox(text='Under Exposed', default=True, key='conf_main_under_exposed_bool', pad=((0, 20), 0)),
            sg.Checkbox(text='Dynamic Range', default=False, key='conf_main_dynamic_range_bool', pad=((0, 20), 0)),
            sg.Checkbox(text='Peak Saturation1', default=False, key='conf_main_peak_saturation1_bool',
                        pad=((0, 20), 0)),
            sg.Checkbox(text='Peak Hue1', default=False, key='conf_main_peak_hue1_bool', pad=((0, 20), 0)),
        ],
        [
            sg.Checkbox(text='Peak Saturation2', default=False, key='conf_main_peak_saturation2_bool',
                        pad=((0, 20), 0)),
            sg.Checkbox(text='Peak Hue2', default=False, key='conf_main_peak_hue2_bool', pad=((0, 20), 0)),
            sg.Checkbox(text='Sharpness', default=True, key='conf_main_sharpness_bool', pad=((0, 20), 0)),
            sg.Checkbox(text='ISO', default=True, key='conf_main_iso_bool', pad=((0, 20), 0)),
            sg.Checkbox(text='ET', default=True, key='conf_main_et_bool', pad=((0, 20), 0)),
        ]
    ]
    #     "summary_params": {
    #         "af": True,
    #         "ae": True,
    #         "awb": True,
    #         "colors": True,
    #         "noise": True,
    #         "details": True,
    #         "artifacts": True,
    #         "torch": True,
    #         "flash": True
    #     },
    conf_summ_params_layout = [
        [
            sg.Checkbox(text='AF', default=True, key='conf_summ_params_af_bool', pad=((0, 20), 0)),
            sg.Checkbox(text='AE', default=True, key='conf_summ_params_ae_bool', pad=((0, 20), 0)),
            sg.Checkbox(text='AWB', default=True, key='conf_summ_params_awb_bool', pad=((0, 20), 0)),
            sg.Checkbox(text='Colors', default=True, key='conf_summ_params_colors_bool', pad=((0, 20), 0)),
            sg.Checkbox(text='Noise', default=True, key='conf_summ_params_noise_bool', pad=((0, 20), 0)),
            sg.Checkbox(text='Details', default=True, key='conf_summ_params_details_bool', pad=((0, 20), 0)),
        ],
        [
            sg.Checkbox(text='Artifacts', default=True, key='conf_summ_params_artifacts_bool', pad=((0, 20), 0)),
            sg.Checkbox(text='Torch', default=True, key='conf_summ_params_torch_bool', pad=((0, 20), 0)),
            sg.Checkbox(text='Flash', default=True, key='conf_summ_params_flash_bool', pad=((0, 20), 0)),
        ],
    ]

    #     "summary_items": {
    #         "attribute": True,
    #         "level": True,
    #         "issues": True,
    #         "suggestions": True
    #     },
    conf_summ_items_layout = [
        [
            sg.Checkbox(text='Attribute', default=True, key='conf_summ_items_attribute_bool', pad=((0, 20), 0)),
            sg.Checkbox(text='Level', default=True, key='conf_summ_items_level_bool', pad=((0, 20), 0)),
            sg.Checkbox(text='Issues', default=True, key='conf_summ_items_issues_bool', pad=((0, 20), 0)),
            sg.Checkbox(text='Suggestions', default=True, key='conf_summ_items_suggestions_bool', pad=((0, 20), 0)),
        ],
    ]

    #     "attribute": {
    #         "exposure": True,
    #         "colors": True,
    #         "noise": True,
    #         "details": True,
    #         "artifacts": True
    #     }
    conf_attribute_layout = [[
        sg.Checkbox(text='Exposure', default=True, key='conf_attribute_exposure_bool', pad=((0, 20), 0)),
        sg.Checkbox(text='Colors', default=True, key='conf_attribute_colors_bool', pad=((0, 20), 0)),
        sg.Checkbox(text='Noise', default=True, key='conf_attribute_noise_bool', pad=((0, 20), 0)),
        sg.Checkbox(text='Details', default=True, key='conf_attribute_details_bool', pad=((0, 20), 0)),
        sg.Checkbox(text='Artifacts', default=True, key='conf_attribute_artifacts_bool', pad=((0, 20), 0)),
    ], ]

    reallife_frame_layout = [
        [
            sg.T('Images dir:', size=(18, 1)),
            sg.Input(key='rlt_report_input_files', readonly=True, size=(36, 1), enable_events=True),
            sg.FolderBrowse(size=(8, 1), key='rlt_report_output_browse', target='rlt_report_input_files')
        ], [
            sg.T('Presentation Name:', size=(18, 1)),
            sg.Input(key='rlt_report_name', size=(36, 1)),
        ],
        # First Collapsable
        [
            sg.T(constants.SYMBOL_DOWN if opened_conf_main else constants.SYMBOL_UP,
                 enable_events=True, k='-OPEN SEC_CONF_MAIN-',
                 text_color=constants.PRIMARY_COLOR),
            sg.T('Main',
                 enable_events=True,
                 text_color=constants.PRIMARY_COLOR,
                 k='-OPEN SEC_CONF_MAIN-TEXT-',
                 pad=((0, 20), 0)),

            sg.T(constants.SYMBOL_DOWN if opened_conf_summ_params else constants.SYMBOL_UP,
                 enable_events=True, k='-OPEN SEC_CONF_SUMM_PARAMS-',
                 text_color=constants.PRIMARY_COLOR),
            sg.T('Summary Params',
                 enable_events=True,
                 text_color=constants.PRIMARY_COLOR,
                 k='-OPEN SEC_CONF_SUMM_PARAMS-TEXT-',
                 pad=((0, 20), 0)),

            sg.T(constants.SYMBOL_DOWN if opened_conf_summ_items else constants.SYMBOL_UP,
                 enable_events=True, k='-OPEN SEC_CONF_SUMM_ITEMS-',
                 text_color=constants.PRIMARY_COLOR),
            sg.T('Summary Items',
                 enable_events=True,
                 text_color=constants.PRIMARY_COLOR,
                 k='-OPEN SEC_CONF_SUMM_ITEMS-TEXT-',
                 pad=((0, 20), 0)),

            sg.T(constants.SYMBOL_DOWN if opened_conf_attribute else constants.SYMBOL_UP,
                 enable_events=True, k='-OPEN SEC_CONF_ATTRIBUTE-',
                 text_color=constants.PRIMARY_COLOR),
            sg.T('Attributes',
                 enable_events=True,
                 text_color=constants.PRIMARY_COLOR,
                 k='-OPEN SEC_CONF_ATTRIBUTE-TEXT-',
                 pad=((0, 20), 0))

        ],
        # First Collapsable
        [collapse(conf_main_layout,
                  '-SEC_CONF_MAIN-',
                  visible=opened_conf_main)],

        # Second Collapsable
        [collapse(conf_summ_params_layout,
                  '-SEC_CONF_SUMM_PARAMS-',
                  visible=opened_conf_summ_params)],

        # Third Collapsable
        [collapse(conf_summ_items_layout,
                  '-SEC_CONF_SUMM_ITEMS-',
                  visible=opened_conf_summ_params)],

        # Fourth Collapsable
        [collapse(conf_attribute_layout,
                  '-SEC_CONF_ATTRIBUTE-',
                  visible=opened_conf_attribute)],

        [sg.Button("Generate",
                   key='rlt_report_build_btn',
                   size=(20, 1),
                   disabled=True)]
    ]

    # All the stuff inside your window.
    tab_main = [
        [sg.Frame('Devices', devices_frame, font='Any 12')],
        [sg.Frame('Settings', device_settings_frame_layout, font='Any 12')],
        [sg.Frame('Device Tools', device_tools_layout, font='Any 12')],
        [sg.Frame('Lights', lights_frame_layout, font='Any 12')],
        [
            sg.Button('Capture Cases (Manual)', size=(25, 2), key='capture_manual_btn', disabled=True),
            sg.Button('Capture Cases (Automated)', size=(30, 2), key='capture_auto_btn', disabled=True),
            sg.Button('?', size=(4, 2), key='help_btn', disabled=False)
        ]
    ]

    loading_status_bar_layout = [
        [
            sg.ProgressBar(max_value=100, orientation='h', size=(22, 10), visible=True, key='progressbar'),
            sg.T("0", justification='right', size=(3, 1), pad=(0, 0), key='progressbar_percent'), sg.T("%"),
            sg.T("Loading", size=(17, 1), key='progressbar_status')
        ]
    ]

    tab2_layout = [
        [sg.Frame('Objective Tests Reporting', objective_frame_layout, font='Any 12')],
        [sg.Frame('Real-Life Tests Reporting', reallife_frame_layout, font='Any 12')]
    ]

    tab3_layout = [
        [
            sg.Button('Generate Project Requirements File', size=(30, 2), key='project_req_tool_btn', pad=(15, 15)),
        ],
        [
            sg.Button('Extract Frames From Video', size=(30, 2), key='extract_video_frames_tool_btn', pad=(15, 15))
        ],
        [
            sg.Button('Test USB Camera', size=(30, 2), key='usb_cam_tool_btn', pad=(15, 15), visible=constants.DEBUG_MODE)
        ],

        # [sg.T('RAW Converter')],
        # [sg.T('ISP Simulator')],
    ]

    layout = [
        [sg.Image(os.path.join(constants.ROOT_DIR, 'images', 'automated-video-testing-header.png'))],
        [
            Tabs([
                [
                    sg.Tab('Testing', tab_main),
                    sg.Tab('Reporting', tab2_layout),
                    sg.Tab('Tools', tab3_layout),
                ]],
                key='main_tabs_group',
            )],
        [
            sg.Button('Exit', size=(20, 1)),
            sg.Text('App Version: {}'.format(constants.APP_VERSION), size=(40, 1), justification="right")
        ],
        [
            collapse(loading_status_bar_layout, 'loading_status_bar')
        ]
    ]

    # Create the Window
    window = sg.Window(
        'Automated Photo/Video Testing',
        layout,
        icon=os.path.join(constants.ROOT_DIR, 'images', 'automated-video-testing-header-icon.ico'),
        no_titlebar=False,
        grab_anywhere=False
    )

    # Watchdogs
    devices_watchdog_event = '-DEVICES-WATCHDOG-'

    adb = AdbClient(gui_window=window, gui_event=devices_watchdog_event)
    adb.watchdog()
    adb_devices = adb.devices_obj  # List to store devices objects

    # usbcam_client = USBCamClient(gui_window=window, gui_event=devices_watchdog_event)
    # usbcam_client.watchdog()
    # usbcam_devices = usbcam_client.devices_obj

    reports_loading_event = None
    obj_reports_event = "RLTReport_Thread"
    rlt_reports_event = "RLTReport_Thread"

    progress_bar = window['progressbar']
    progress_bar_percent = window['progressbar_percent']
    progress_bar_status = window['progressbar_status']

    # Event Loop to process "events" and get the "values" of the inputs
    while True:
        event, values = window.read()

        if event == sg.WIN_CLOSED or event == 'Exit':  # if user closes window or clicks cancel
            break

        # print('Data: ', values)  # Debugging
        logger.debug(f'Event: {event}')  # Debugging
        logger.debug(f"Selected tab: {values['main_tabs_group']}")
        # print('ADB List Devices', devices_list)  # Debugging
        # print('Devices objects: ', device)

        # ---- Devices Listing
        if event == devices_watchdog_event:
            watchdog_received = values[devices_watchdog_event]

            if watchdog_received['action'] == 'connected':
                # Connected
                for num in range(constants.MAX_DEVICES_AT_ONE_RUN):
                    try:
                        if values[f'device_serial.{num}'] == '' or \
                                values[f'device_serial.{num}'] == watchdog_received['serial']:
                            device_data = watchdog_received
                            del device_data['error'], device_data['action']

                            logger.debug("setting {} to row {}".format(watchdog_received['serial'], num))

                            window[f'device_attached.{num}'].Update(text=watchdog_received['serial'],
                                                                    text_color='black',
                                                                    background_color='yellow',
                                                                    disabled=False,
                                                                    visible=True)
                            window[f'device_attached.{num}'].metadata = device_data
                            window[f'device_serial.{num}'].Update(watchdog_received['serial'])  # TODO: Deprecate this
                            window[f'device_icon.{num}'].Update(
                                filename=constants.DEVICE_ICONS[watchdog_received['type']],
                                visible=True)

                            window[f'device_friendly.{num}'].Update(visible=True)
                            window[f'identify_device_btn.{num}'].Update(visible=True)
                            window[f'ctrl_device_btn.{num}'].Update(visible=True)

                            logger.debug(f"metadata: {window[f'device_attached.{num}'].metadata}")
                            break
                    except KeyError:
                        logger.critical('Devices limit exceeded! \nnum: {num}, max: {constants.MAX_DEVICES_AT_ONE_RUN}')
            elif watchdog_received['action'] == 'disconnected':
                # If device is disconnected
                for num in range(constants.MAX_DEVICES_AT_ONE_RUN):
                    if values[f'device_serial.{num}'] == watchdog_received['serial']:
                        window[f'device_attached.{num}'].Update(value=False, background_color='red', disabled=True,
                                                                visible=False)
                        window[f'device_friendly.{num}'].Update(disabled=True, visible=False)
                        window[f'identify_device_btn.{num}'].Update(visible=False)
                        window[f'ctrl_device_btn.{num}'].Update(visible=False)
                        window[f'device_icon.{num}'].Update(visible=False)
                        break
                try:
                    logger.info('device disconnected, detaching')
                    adb.detach_device(watchdog_received['serial'])
                    del adb_devices[watchdog_received['serial']]
                except KeyError:
                    logger.info("Wasn't attached anyway..")

        attached_devices_list = adb.get_attached_devices()

        if event.split('.')[0] == 'device_attached':
            diff_device = values[f"device_serial.{event.split('.')[1]}"]
            if values[f"device_attached.{event.split('.')[1]}"]:  # Attach device
                # Add device to attached devices list
                try:
                    adb.attach_device(diff_device)
                except ValueError as e:
                    logger.exception("Error while attaching to device...")
                    sg.popup_error("Error while attaching to device...\n", e)
                    logger.debug(adb.attached_devices)
                    # This next line fixes an issue that it tries to attach device after fail if you try again
                    window[f"device_attached.{event.split('.')[1]}"].Update(False)
                    continue

                try:
                    for num in range(constants.MAX_DEVICES_AT_ONE_RUN):
                        if values[f'device_serial.{num}'] == diff_device or values[f'device_serial.{num}'] == '':
                            window[f'device_attached.{num}'].Update(text_color='white', background_color='green')
                            window[f'device_friendly.{num}'].Update(text_color='white',
                                                                    background_color='green',
                                                                    value=adb_devices[diff_device].friendly_name,
                                                                    disabled=False)
                            window[f'identify_device_btn.{num}'].Update(disabled=False)
                            window[f'ctrl_device_btn.{num}'].Update(disabled=False)
                            break

                    logger.info('Added {} to attached devices!'.format(diff_device))

                    logger.info('Currently opened app: {}'.format(adb_devices[diff_device].get_current_app()))
                except KeyError as e:
                    logger.error(f"adb_devices key error: {e}\nadb_devices: {adb_devices}")
            else:  # Detach
                logger.info('User wanted to detach device...')
                adb.detach_device(diff_device)

                for num in range(constants.MAX_DEVICES_AT_ONE_RUN):
                    if values[f'device_serial.{num}'] == diff_device or values[f'device_serial.{num}'] == '':
                        window[f'device_attached.{num}'].Update(text_color='black', background_color='yellow')
                        window[f'device_friendly.{num}'].Update(text_color='black', background_color='yellow')
                        window[f'identify_device_btn.{num}'].Update(disabled=True)
                        window[f'ctrl_device_btn.{num}'].Update(disabled=True)
                        break

                logger.info('{} was detached!'.format(diff_device))

        # ---- Devices Listing Ends here

        if attached_devices_list:
            # At least one device is attached!

            # Disable/Enable buttons
            window['camxoverride_btn'].Update(disabled=False)
            window['reboot_device_btn'].Update(disabled=False)
            window['push_file_btn'].Update(disabled=False)
            window['pull_file_btn'].Update(disabled=not constants.DEBUG_MODE)
            window['record_screen_btn'].Update(disabled=False)
            window['setup_device_btn'].Update(disabled=False)
            window['capture_manual_btn'].Update(disabled=False)
            window['capture_auto_btn'].Update(disabled=False)
            if event.split('.')[0] == 'identify_device_btn':  # Identify Buttons
                logger.info('Identifying ' + event.split('.')[1])
                device000 = values[f"device_serial.{event.split('.')[1]}"]
                adb_devices[device000].identify()
            if event.split('.')[0] == 'ctrl_device_btn':  # Device Control
                logger.info('Opening device control for ' + event.split('.')[1])
                device000 = values[f"device_serial.{event.split('.')[1]}"]
                adb_devices[device000].open_device_ctrl()

            # Buttons callbacks
            if event == "camxoverride_btn":
                gui_camxoverride(attached_devices_list, adb_devices)

            if event == "push_file_btn":
                gui_push_file(attached_devices_list, adb_devices)

            if event == "pull_file_btn":
                gui_android_file_browser(attached_devices_list, adb_devices, pull_button=True)

            if event == "record_screen_btn":
                gui_screenrec(attached_devices_list, adb_devices)

            if event == "setup_device_btn":
                gui_setup_device(attached_devices_list, adb_devices)

            if event.split('.')[0] == 'device_friendly':
                device000 = values[f"device_serial.{event.split('.')[1]}"]
                adb_devices[device000].friendly_name = values[f"device_friendly.{event.split('.')[1]}"]
                logger.debug(f'for {device000} fr name is {adb_devices[device000].friendly_name}')

            if event == 'reboot_device_btn':
                gui_reboot_device(attached_devices_list, adb_devices)

            if event == 'capture_manual_btn':
                gui_manual_cases(attached_devices_list, adb_devices)

            if event == 'capture_auto_btn':
                logger.info('Launching GUI')
                gui_automated_cases(adb, values['selected_lights_model'],
                                    values['selected_luxmeter_model'])

        else:
            # print('No attached devices!')
            window['camxoverride_btn'].Update(disabled=True)
            window['reboot_device_btn'].Update(disabled=True)
            window['push_file_btn'].Update(disabled=True)
            window['pull_file_btn'].Update(disabled=True)
            window['record_screen_btn'].Update(disabled=True)
            window['setup_device_btn'].Update(disabled=True)
            window['capture_manual_btn'].Update(disabled=True)
            window['capture_auto_btn'].Update(disabled=True)

        if event == 'test_lights_btn':
            gui_test_lights(values['selected_lights_model'], values['selected_luxmeter_model'])

        if event == 'help_btn':
            gui_help()

        # ####################
        # Tools tab

        if event == 'project_req_tool_btn':
            gui_project_req_file()

        if event == 'extract_video_frames_tool_btn':
            gui_extract_video_frames_tool()

        if event == 'usb_cam_tool_btn':
            gui_cam_tool()

        # ####################
        # Reports tab
        tab2_elems = [
            'loading_status_bar',
            'obj_report_projreq_btn', 'obj_report_output_browse', 'obj_report_build_btn',
            'rlt_report_build_btn', 'rlt_report_output_browse'
        ]

        # ##########
        # Objective Reports

        # Grabbing Project requirements
        if event == 'obj_report_projreq_btn':
            try:
                ret_data
            except NameError:
                pass_file = pass_dict = ret_data = None
            else:
                if isinstance(ret_data, dict):
                    pass_dict = ret_data['dict']
                    pass_file = values['obj_report_projreq_field']
                else:
                    pass_file = pass_dict = None

            ret_data = gui_project_req_file(proj_req=pass_dict, proj_req_file=pass_file, return_val=True)
            if ret_data is not None:
                templ_data = ret_data['dict']
                if ret_data['projreq_file'] is not None:
                    window['obj_report_projreq_field'].Update(ret_data['projreq_file'])
                else:
                    window['obj_report_projreq_field'].Update('New unsaved file')

        # Disable Build btn when output field is empty
        if event == 'obj_report_output':
            window['obj_report_build_btn'].Update(
                disabled=not (ret_data is not None and values['obj_report_output'] != ''))

        # On Build btn press
        if event == 'obj_report_build_btn':
            generate_obj_report(
                templ_data, values['obj_report_projreq_field'], values['obj_report_output'], window, rlt_reports_event
            )
            reports_loading_event = obj_reports_event

        # ##########
        # RLT Reports

        # Disable/Enable Go button based on files field
        if event == 'rlt_report_input_files':
            window['rlt_report_build_btn'].Update(disabled=not (values['rlt_report_input_files'] != ''))

        # Dropdowns
        if event.startswith('-OPEN SEC_CONF_MAIN'):
            opened_conf_main, opened_conf_summ_params, opened_conf_summ_items, opened_conf_attribute = not opened_conf_main, False, False, False
        elif event.startswith('-OPEN SEC_CONF_SUMM_PARAMS'):
            opened_conf_main, opened_conf_summ_params, opened_conf_summ_items, opened_conf_attribute = False, not opened_conf_summ_params, False, False
        elif event.startswith('-OPEN SEC_CONF_SUMM_ITEMS'):
            opened_conf_main, opened_conf_summ_params, opened_conf_summ_items, opened_conf_attribute = False, False, not opened_conf_summ_items, False
        elif event.startswith('-OPEN SEC_CONF_ATTRIBUTE'):
            opened_conf_main, opened_conf_summ_params, opened_conf_summ_items, opened_conf_attribute = False, False, False, not opened_conf_attribute

        window['-OPEN SEC_CONF_MAIN-'].update(constants.SYMBOL_DOWN if opened_conf_main else constants.SYMBOL_UP)
        window['-SEC_CONF_MAIN-'].update(visible=opened_conf_main)

        window['-OPEN SEC_CONF_SUMM_PARAMS-'].update(
            constants.SYMBOL_DOWN if opened_conf_summ_params else constants.SYMBOL_UP)
        window['-SEC_CONF_SUMM_PARAMS-'].update(visible=opened_conf_summ_params)

        window['-OPEN SEC_CONF_SUMM_ITEMS-'].update(
            constants.SYMBOL_DOWN if opened_conf_summ_items else constants.SYMBOL_UP)
        window['-SEC_CONF_SUMM_ITEMS-'].update(visible=opened_conf_summ_items)

        window['-OPEN SEC_CONF_ATTRIBUTE-'].update(
            constants.SYMBOL_DOWN if opened_conf_attribute else constants.SYMBOL_UP)
        window['-SEC_CONF_ATTRIBUTE-'].update(visible=opened_conf_attribute)

        # Hit Build RLT Report Button
        if event == 'rlt_report_build_btn':
            report_config = {
                "config": {
                    "image_path": values['rlt_report_input_files'],
                    "thumbnail_path": os.path.join(values['rlt_report_input_files'], "Thumbnails"),
                    "presentation_name": values['rlt_report_name'],
                    "attribute_on": 1,
                    "Avg Luma": values['conf_main_avg_luma_bool'],
                    "Contrast": values['conf_main_contrast_bool'],
                    "Black Level": values['conf_main_black_level_bool'],
                    "White Level": values['conf_main_white_level_bool'],
                    "Over Exposed": values['conf_main_over_exposed_bool'],
                    "Under Exposed": values['conf_main_under_exposed_bool'],
                    "Dynamic Range": values['conf_main_dynamic_range_bool'],
                    "Peak Saturation 1": values['conf_main_peak_saturation1_bool'],
                    "Peak Hue 1": values['conf_main_peak_hue1_bool'],
                    "Peak Saturation 2": values['conf_main_peak_saturation2_bool'],
                    "Peak Hue 2": values['conf_main_peak_hue2_bool'],
                    "Sharpness": values['conf_main_sharpness_bool'],
                    "ISO": values['conf_main_iso_bool'],
                    "ET": values['conf_main_et_bool']
                },
                "summary_params": {
                    "AF": values['conf_summ_params_af_bool'],
                    "AE": values['conf_summ_params_ae_bool'],
                    "AWB": values['conf_summ_params_awb_bool'],
                    "Colors": values['conf_summ_params_colors_bool'],
                    "Noise": values['conf_summ_params_noise_bool'],
                    "Details": values['conf_summ_params_details_bool'],
                    "Artifacts": values['conf_summ_params_artifacts_bool'],
                    "Torch": values['conf_summ_params_torch_bool'],
                    "Flash": values['conf_summ_params_flash_bool']
                },
                "summary_items": {
                    "Attribute": values['conf_summ_items_attribute_bool'],
                    "Level": values['conf_summ_items_level_bool'],
                    "Issues": values['conf_summ_items_issues_bool'],
                    "Suggestions": values['conf_summ_items_suggestions_bool']
                },
                "attribute": {
                    "Exposure": values['conf_attribute_exposure_bool'],
                    "Colors": values['conf_attribute_colors_bool'],
                    "Noise": values['conf_attribute_noise_bool'],
                    "Details": values['conf_attribute_details_bool'],
                    "Artifacts": values['conf_attribute_artifacts_bool']
                }
            }
            logger.debug(f"Report Config: {report_config}")

            generate_rlt_report(report_config, window, rlt_reports_event)
            reports_loading_event = rlt_reports_event

        # ##########
        # Reports Loading Bar

        if event == reports_loading_event:
            gui_received = values[reports_loading_event]
            logger.debug(f'gui loading indicator received: \n{gui_received}')

            # TODO: Make object send errors
            try:
                gui_received['error']
            except KeyError:
                pass
            else:
                if gui_received['error']:
                    sg.popup_scrolled(f"{gui_received['reason']}: \n{gui_received['info']}")
            try:
                gui_received['info']
            except KeyError:
                pass
            else:
                progress_bar_status.Update(gui_received['info'])

            try:
                gui_received['progress']
            except KeyError:
                pass
            else:
                if gui_received['progress'] == 0:
                    # make visible
                    set_buttons(window, tab2_elems, True)

                progress_bar.Update(current_count=gui_received['progress'])
                progress_bar_percent.Update(gui_received['progress'])

                if gui_received['progress'] == 100:
                    done_msg = gui_received['info']
                    new_file = None

                    try:
                        gui_received['new_file']
                    except KeyError:
                        pass
                    else:
                        if gui_received['new_file']:
                            new_file = gui_received['new_file']
                            done_msg += f"\nNew report:\n{new_file}"

                    logger.info(done_msg)
                    sg.popup_ok(done_msg)

                    if new_file:
                        explorer_open_file(new_file)

                    reports_loading_event = None

                    set_buttons(window, tab2_elems, False)
    # Before exiting...

    # Detach attached devices
    logger.info("Detaching attached devices...")
    attached = attached_devices_list.copy()
    for dev in attached:
        logger.info(f"Detaching {dev}")
        adb.detach_device(dev)

    window.close()


def set_buttons(window, elements_list: list, disabledBool: bool):
    # Sets Disabled = True/False to what can be disabled
    # Sets Visible = False/True to what can be hidden

    for elem in elements_list:
        try:
            window[elem].Update(disabled=disabledBool)
        except TypeError:
            window[elem].Update(visible=disabledBool)


def set_gui_theme():
    sg.theme_slider_border_width(0)
    sg.theme_slider_color(constants.GUI_SLIDER_COLOR)
    sg.theme_background_color(constants.GUI_BG_COLOR)
    sg.theme_element_background_color(constants.GUI_ELEMENT_BG_COLOR)
    sg.theme_element_text_color(constants.GUI_ELEMENT_TEXT_COLOR)
    sg.theme_text_color(constants.GUI_TEXT_COLOR)
    sg.theme_text_element_background_color(constants.GUI_BG_COLOR)
    sg.theme_input_text_color(constants.GUI_INPUT_TEXT_COLOR)
    sg.theme_input_background_color(constants.GUI_INPUT_BG_COLOR)
    sg.theme_button_color(
        (constants.GUI_BUTTON_TEXT_COLOR,
         constants.GUI_BUTTON_BG_COLOR)
    )
    sg.theme_border_width(constants.GUI_BORDER_WIDTH)
    sg.theme_progress_bar_border_width(constants.GUI_PROGRESS_BAR_BORDER_WIDTH)
    sg.theme_progress_bar_color((constants.GUI_PROGRESS_BAR_COLOR, '#D0D0D0'))
