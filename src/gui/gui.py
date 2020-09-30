import os

from src.temp.actions import *
from src.app import AdbClient
from src.app.Device import Device

from src.gui.gui_help import gui_help
from src.gui.gui_camxoverride import gui_camxoverride
from src.gui.gui_manual_cases import gui_manual_cases
from src.gui.gui_automated_cases import gui_automated_cases
from src.gui.gui_push_file import gui_push_file
from src.gui.gui_reboot_device import gui_reboot_device
from src.gui.gui_setup_device import gui_setup_device
from src.gui.gui_test_lights import gui_test_lights
import PySimpleGUI as sg

import src.constants as constants

ROOT_DIR = os.path.abspath(os.curdir + "/../")  # This is Project Root


def loading(secs):  # Only gives fanciness
    for i in range(1, 15 * secs):
        sg.popup_animated(image_source=os.path.join(ROOT_DIR, 'images', 'loading3.gif'), message='Loading...',
                          no_titlebar=True,
                          font=('Any', 25), text_color='black',
                          background_color='white',
                          alpha_channel=0.8,
                          )
        time.sleep(0.02)
    sg.popup_animated(image_source=None)


def place(elem):
    """
    Places element provided into a Column element so that its placement in the layout is retained.
    :param elem: the element to put into the layout
    :return: A column element containing the provided element
    """
    return sg.Column([[elem]], pad=(0, 0))


def gui():
    sg.theme('DarkGrey5')  # Add a touch of color

    adb = AdbClient.AdbClient()

    loading(3)

    devices_frame = []
    for num in range(constants.MAX_DEVICES_AT_ONE_RUN):
        print(f"Building row {num}")  # Debugging
        devices_frame += [
                             place(sg.Image(filename='', key=f'device_icon.{num}', visible=False)),
                             place(sg.Checkbox('', key=f'device_attached.{num}',
                                               text_color="black",
                                               disabled=True,
                                               enable_events=True,
                                               visible=False,
                                               size=(17, 1))),
                             place(sg.InputText(key=f'device_serial.{num}',
                                                background_color="red",
                                                size=(15, 1),
                                                readonly=True,
                                                default_text='',
                                                visible=False)),
                             place(sg.InputText(key=f'device_friendly.{num}', enable_events=True, size=(23, 1),
                                                disabled=True,
                                                visible=False)),
                             place(sg.Button('Identify',
                                             button_color=(sg.theme_text_element_background_color(), 'silver'),
                                             key=f'identify_device_btn.{num}',
                                             disabled=True,
                                             enable_events=True,
                                             visible=False)),
                             place(sg.Button('Control',
                                             button_color=(sg.theme_text_element_background_color(), 'silver'),
                                             key=f'ctrl_device_btn.{num}',
                                             disabled=True,
                                             enable_events=True,
                                             visible=False
                                             ))
                         ],

    device_settings_frame_layout = [[
        sg.Button('Edit camxoverridesettings', button_color=(sg.theme_text_element_background_color(), 'silver'),
                  size=(20, 3),
                  key='camxoverride_btn',
                  disabled=True,
                  tooltip='Edit or view camxoverridesettings of any attached device'),
        sg.Button('Push file', button_color=(sg.theme_text_element_background_color(), 'silver'),
                  size=(12, 3),
                  key='push_file_btn',
                  disabled=True),
        sg.Button('Reboot Device', button_color=(sg.theme_text_element_background_color(), 'silver'),
                  size=(12, 3),
                  key='reboot_device_btn',
                  disabled=True,
                  tooltip='Reboot devices immediately'),
        sg.Button('Setup', button_color=(sg.theme_text_element_background_color(), 'silver'),
                  size=(12, 3),
                  key='setup_device_btn',
                  disabled=True,
                  tooltip='Setup device settings, calibrate touch events etc.'),
    ],
    ]

    lights_frame_layout = [[
        sg.OptionMenu(
            values=list(constants.LIGHTS_MODELS.keys()),
            key="selected_lights_model",
            size=(22, 1)
        ),
        sg.OptionMenu(
            values=['None', 'Konita Minolta CL-200A', 'something else'],
            key="selected_luxmeter_model",
            size=(22, 1)
        ),
        sg.Button(
            'Test Lights',
            button_color=(sg.theme_text_element_background_color(), 'silver'),
            size=(11, 3),
            key='test_lights_btn',
            disabled=False
        ),
    ],
    ]

    # All the stuff inside your window.
    tab_main = [
        [sg.Image(os.path.join(ROOT_DIR, 'images', 'automated-video-testing-header.png'))],
        [sg.Frame('Devices', devices_frame, font='Any 12', title_color='white')],
        [sg.Frame('Settings', device_settings_frame_layout, font='Any 12', title_color='white')],
        [sg.Frame('Lights', lights_frame_layout, font='Any 12', title_color='white')],
        [
            sg.Button('Capture Cases (Manual)', size=(25, 2), key='capture_manual_btn', disabled=True),
            sg.Button('Capture Cases (Automated)', size=(31, 2), key='capture_auto_btn', disabled=True),
            sg.Button('?', size=(4, 2), key='help_btn', disabled=False)
        ]
    ]

    tab2_layout = [
        [sg.T('Real-Life Reporting')],
        [sg.T('Objective Reporting')]
    ]

    tab3_layout = [
        [sg.T('RAW Converter')],
        [sg.T('ISP Simulator')],
    ]

    layout = [
        [sg.TabGroup([[
            sg.Tab('Testing', tab_main),
            sg.Tab('Reporting', tab2_layout),
            sg.Tab('Tools', tab3_layout),
        ]])],
        [
            sg.Button('Exit', size=(20, 1)),
            sg.Text('App Version: {}'.format(constants.APP_VERSION), size=(43, 1), justification="right")
        ]
    ]

    # Create the Window
    window = sg.Window('Automated Photo/Video Testing', layout,
                       icon=os.path.join(ROOT_DIR, 'images', 'automated-video-testing-header-icon.ico'))
    devices = {}  # List to store devices objects
    devices_list_old = []  # set devices_list_old empty so that se can find devices from first run

    # Event Loop to process "events" and get the "values" of the inputs
    while True:
        event, values = window.read(timeout=100)
        devices_list = adb.list_devices()
        attached_devices_list = adb.get_attached_devices()

        if event == sg.WIN_CLOSED or event == 'Exit':  # if user closes window or clicks cancel
            break

        # print('Data: ', values)  # Debugging
        # print('Event: ', event)  # Debugging
        # print('ADB List Devices', devices_list)  # Debugging
        # print('Devices objects: ', device)

        try:
            if len(devices_list) > len(devices_list_old):  # If New devices found
                for count, diff_device in enumerate([str(s) for s in (set(devices_list_old) ^ set(devices_list))]):
                    print("Found new device!!! -> ", diff_device)

                    for numm in range(constants.MAX_DEVICES_AT_ONE_RUN):
                        num = numm + count
                        try:
                            if values[f'device_serial.{num}'] == '' or values[f'device_serial.{num}'] == diff_device:
                                print("setting {} to row {}".format(diff_device, num))

                                window[f'device_attached.{num}'].Update(text=diff_device,
                                                                        background_color='yellow',
                                                                        disabled=False,
                                                                        visible=True)
                                window[f'device_serial.{num}'].Update(diff_device)
                                window[f'device_icon.{num}'].Update(
                                    filename=os.path.join(ROOT_DIR, 'images', 'device-icons', 'android-flat-32.png'),
                                    visible=True)

                                window[f'device_friendly.{num}'].Update(visible=True)
                                window[f'identify_device_btn.{num}'].Update(visible=True)
                                window[f'ctrl_device_btn.{num}'].Update(visible=True)
                                break
                        except KeyError:
                            print('Devices limit exceeded!')
                            print(f'numm: {numm}, num: {num}, count: {count}, max: {constants.MAX_DEVICES_AT_ONE_RUN}')
            elif len(devices_list) < len(devices_list_old):  # If device is disconnected
                for count, diff_device in enumerate([str(s) for s in (set(devices_list_old) ^ set(devices_list))]):
                    print("Device detached :( -> ", diff_device)

                    # window['devices'].update(values=devices_list)
                    for numm in range(constants.MAX_DEVICES_AT_ONE_RUN):
                        num = numm + count
                        if values[f'device_serial.{num}'] == diff_device:
                            window[f'device_attached.{num}'].Update(value=False, background_color='red', disabled=True,
                                                                    visible=False)
                            window[f'device_friendly.{num}'].Update(disabled=True, visible=False)
                            window[f'identify_device_btn.{num}'].Update(visible=False)
                            window[f'ctrl_device_btn.{num}'].Update(visible=False)
                            window[f'device_icon.{num}'].Update(visible=False)
                            break
                    try:
                        adb.detach_device(diff_device, devices[diff_device])
                        del devices[diff_device]
                    except KeyError:
                        print("Wasn't attached anyway..")
        except UnboundLocalError:
            pass  # devices_list_old not set yet. No worries, will be set on next run of loop.

        devices_list_old = devices_list

        if event.split('.')[0] == 'device_attached':
            diff_device = values[f"device_serial.{event.split('.')[1]}"]

            if values[f"device_attached.{event.split('.')[1]}"]:  # Attach device
                devices[diff_device] = Device(adb, diff_device)  # Assign device to object

                for num in range(constants.MAX_DEVICES_AT_ONE_RUN):
                    if values[f'device_serial.{num}'] == diff_device or values[f'device_serial.{num}'] == '':
                        window[f'device_attached.{num}'].Update(background_color='green')
                        window[f'device_friendly.{num}'].Update(background_color='green',
                                                                value=devices[diff_device].friendly_name,
                                                                disabled=False)
                        window[f'identify_device_btn.{num}'].Update(disabled=False)
                        window[f'ctrl_device_btn.{num}'].Update(disabled=False)
                        break

                print('Added {} to attached devices!'.format(diff_device))

                print('Currently opened app: {}'.format(devices[diff_device].get_current_app()))
            else:  # Detach
                adb.detach_device(diff_device, devices[diff_device])
                del devices[diff_device]

                for num in range(constants.MAX_DEVICES_AT_ONE_RUN):
                    if values[f'device_serial.{num}'] == diff_device or values[f'device_serial.{num}'] == '':
                        window[f'device_attached.{num}'].Update(background_color='yellow')
                        window[f'device_friendly.{num}'].Update(background_color='yellow')
                        window[f'identify_device_btn.{num}'].Update(disabled=True)
                        window[f'ctrl_device_btn.{num}'].Update(disabled=True)
                        break

                print('{} was detached!'.format(diff_device))

        if attached_devices_list:
            # print('At least one device is attached!') # Debugging

            # Disable/Enable buttons
            window['camxoverride_btn'].Update(disabled=False)
            window['reboot_device_btn'].Update(disabled=False)
            window['push_file_btn'].Update(disabled=False)
            window['setup_device_btn'].Update(disabled=False)
            window['capture_manual_btn'].Update(disabled=False)
            window['capture_auto_btn'].Update(disabled=False)
            if event.split('.')[0] == 'identify_device_btn':  # Identify Buttons
                print('Identifying ' + event.split('.')[1])
                device000 = values[f"device_serial.{event.split('.')[1]}"]
                devices[device000].identify()
            if event.split('.')[0] == 'ctrl_device_btn':  # Device Control
                print('Opening device control for ' + event.split('.')[1])
                device000 = values[f"device_serial.{event.split('.')[1]}"]
                devices[device000].open_device_ctrl()

            # Buttons callbacks
            if event == "camxoverride_btn":
                gui_camxoverride(attached_devices_list, devices)

            if event == "push_file_btn":
                gui_push_file(attached_devices_list, devices)

            if event == "setup_device_btn":
                gui_setup_device(attached_devices_list, devices)

            if event.split('.')[0] == 'device_friendly':
                device000 = values[f"device_serial.{event.split('.')[1]}"]
                devices[device000].friendly_name = values[f"device_friendly.{event.split('.')[1]}"]
                print(f'for {device000} fr name is {devices[device000].friendly_name}')

            if event == 'reboot_device_btn':
                gui_reboot_device(attached_devices_list, devices)

            if event == 'capture_manual_btn':
                # gui_manual_cases(attached_devices_list, devices)
                print(devices[attached_devices_list[0]].get_camera_files_list())

            if event == 'capture_auto_btn':
                print('Launching GUI')
                gui_automated_cases(attached_devices_list, devices, values['selected_lights_model'],
                                    values['selected_luxmeter_model'])

        else:
            # print('No attached devices!')
            window['camxoverride_btn'].Update(disabled=True)
            window['reboot_device_btn'].Update(disabled=True)
            window['push_file_btn'].Update(disabled=True)
            window['setup_device_btn'].Update(disabled=True)
            window['capture_manual_btn'].Update(disabled=True)
            window['capture_auto_btn'].Update(disabled=True)

        if event == 'test_lights_btn':
            gui_test_lights(values['selected_lights_model'], values['selected_luxmeter_model'])

        if event == 'help_btn':
            gui_help()

    # Detach attached devices
    print("Detaching attached devices...")
    attached = attached_devices_list.copy()
    for dev in attached:
        print(f"Detaching {dev}")
        adb.detach_device(dev, devices[dev])

    window.close()
