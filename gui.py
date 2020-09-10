from actions import *
from device import Device
import AdbClient
import threading
import os
from pathlib import Path
import PySimpleGUI as sg

APP_VERSION = '0.01 Beta'
THREAD_EVENT = '-WATCHDOG-'


def devices_watchdog(window):  # TODO
    """
    The thread that communicates with the application through the window's events.

    Once a second wakes and sends a new event and associated value to the window
    """
    i = 0
    while True:
        time.sleep(1)
        window.write_event_value(THREAD_EVENT, (
            threading.current_thread().name, i))  # Data sent is a tuple of thread name and counter
        print('This is cheating from the thread')
        i += 1


def gui_camxoverride(attached_devices, device_obj):
    print("Pulling camxoverridesettings.txt from device...")
    device_obj[attached_devices[0]].pull_file('/vendor/etc/camera/camxoverridesettings.txt',
                                               r'.\tmp\camxoverridesettings.txt')

    camxoverride_content = open(r'.\tmp\camxoverridesettings.txt', 'r').read()

    # All the stuff inside your window.
    layout = [
        [sg.Combo(attached_devices, size=(20, 20), key='selected_device', default_value=attached_devices[0],
                  enable_events=True)],
        [sg.Text('camxoverridesettings.txt:')],
        [sg.Multiline(camxoverride_content, size=(70, 30), key='camxoverride_input')],
        [sg.CloseButton('Close'),
         sg.Button('Save')
         ]
    ]

    # Create the Window
    window = sg.Window('Edit camxoverridesettings', layout,
                       icon=r'.\images\automated-video-testing-header-icon.ico')

    while True:
        event, values = window.read()

        if event == sg.WIN_CLOSED or event == 'Close':  # if user closes window or clicks cancel
            try:
                os.remove(r'.\tmp\camxoverridesettings.txt')
                os.remove(r'.\tmp\camxoverridesettings_new.txt')
            except FileNotFoundError:
                pass
            break

        if event == 'selected_device':
            try:
                os.remove(r'.\tmp\camxoverridesettings.txt')
                os.remove(r'.\tmp\camxoverridesettings_new.txt')
            except FileNotFoundError:
                pass

            print("Pulling camxoverridesettings.txt from device...")
            device_obj[values['selected_device']].pull_file('/vendor/etc/camera/camxoverridesettings.txt',
                                                            r'.\tmp\camxoverridesettings.txt')
            camxoverride_content = open(r'.\tmp\camxoverridesettings.txt', 'r').read()
            window['camxoverride_input'].Update(camxoverride_content)

        if event == 'Save':
            print(values)

            print("Saving camxoverridesettings...")

            print("Generating new camxoverridesettings.txt...")
            camxoverride_new = open(r'.\tmp\camxoverridesettings_new.txt', "w")
            camxoverride_new.write(values['camxoverride_input'])
            camxoverride_new.close()

            device_obj[values['selected_device']].remount()

            print("Pushing new camxoverridesettings.txt file to device...")
            device_obj[values['selected_device']].push_file(r'.\tmp\camxoverridesettings_new.txt',
                                                            "/vendor/etc/camera/camxoverridesettings.txt")

    window.close()


def gui_push_file(attached_devices, device_obj):
    file_destinations = [
        'sdcard/DCIM/',
        'vendor/lib/camera/'
    ]

    layout = [
        [
            sg.Combo(attached_devices, size=(20, 20), key='selected_device', default_value=attached_devices[0]),
            sg.Combo(file_destinations, size=(20, 20), key='dest_folder', default_value=file_destinations[0])
        ],
        [
            sg.Text('File:', size=(11, 1)),
            sg.InputText(size=(35, 1), key='source_file', enable_events=True),
            sg.FileBrowse()
        ],
        [sg.Button('Push File', button_color=(sg.theme_text_element_background_color(), 'silver'), size=(10, 2),
                   key='push_file_btn', disabled=True)]
    ]

    # Create the Window
    window = sg.Window('Push file file', layout,
                       icon=r'.\images\automated-video-testing-header-icon.ico')

    while True:
        event, values = window.read()
        print(values)  # Debugging

        if event == sg.WIN_CLOSED or event == 'Close':  # if user closes window or clicks cancel
            break

        if event == 'source_file':
            window['push_file_btn'].Update(disabled=False)

        if event == 'push_file_btn':
            curr_device = device_obj[values['selected_device']]
            file_dest = values['dest_folder']
            filename = Path(values['source_file']).name

            print("Remounting Device...")
            curr_device.remount()

            print("Pushing new file to device...")

            curr_device.push_file(values['source_file'], file_dest + filename)

    window.close()


def gui_reboot_device(attached_devices, device_obj):
    layout = [
        [sg.Combo(attached_devices, size=(20, 20), key='selected_device', default_value=attached_devices[0])],
        [sg.Button('Reboot', button_color=(sg.theme_text_element_background_color(), 'silver'), size=(10, 2),
                   key='reboot_device_btn', disabled=False)]
    ]

    # Create the Window
    window = sg.Window('Reboot Device', layout,
                       icon=r'.\images\automated-video-testing-header-icon.ico')

    while True:
        event, values = window.read()
        print(values)  # Debugging

        if event == sg.WIN_CLOSED or event == 'Close':  # if user closes window or clicks cancel
            break

        if event == 'reboot_device_btn':
            curr_device = device_obj[values['selected_device']]

            print("Rebooting Device ", values['selected_device'])
            curr_device.reboot()

    window.close()


def gui_setup_device(attached_devices, device_obj):
    select_device_frame = [[
        sg.Combo(attached_devices, size=(20, 20), key='selected_device', default_value=attached_devices[0])
    ],]

    select_app_frame = [[
        sg.Combo(device_obj[attached_devices[0]].get_installed_packages(), size=(40, 1), key='selected_app_package', default_value=device_obj[attached_devices[0]].get_current_app()[0]),
        sg.Button('Test it!', button_color=(sg.theme_text_element_background_color(), 'silver'), size=(10, 1),
                  key='test_app_btn', disabled=False)
    ],]

    photo_sequence_frame = [[
        sg.Combo(list(device_obj[attached_devices[0]].get_clickable_window_elements().keys()), size=(40, 1), key='photo_selected_action.0'),
        sg.Button('Test it!', button_color=(sg.theme_text_element_background_color(), 'silver'), size=(10, 1),
                  key='test_btn_photo_selected_action.0', disabled=False)
    ],]

    layout = [
        [sg.Frame('Select device', select_device_frame, font='Any 12', title_color='white')],
        [sg.Frame('Select Camera App', select_app_frame, font='Any 12', title_color='white')],
        [sg.Frame('Take Photo Action Sequence', photo_sequence_frame, font='Any 12', title_color='white')],
        [sg.Button('Save Settings', button_color=(sg.theme_text_element_background_color(), 'silver'), size=(10, 2),
                   key='save_btn', disabled=False)]
    ]

    # Create the Window
    window = sg.Window('Setup', layout,
                       icon=r'.\images\automated-video-testing-header-icon.ico')


    while True:
        event, values = window.read()
        print(values)  # Debugging

        if event == sg.WIN_CLOSED or event == 'Close':  # if user closes window or clicks cancel
            break

        if event == 'test_app_btn':
            device_obj[values['selected_device']].open_app(values['selected_app_package'])

        if event == 'save_btn':
            # print(device_obj[attached_devices[0]].get_clickable_window_elements().keys())
            pass

        if event.split('.')[0] == 'test_btn_photo_selected_action':
            try:
                data = device_obj[values['selected_device']].get_clickable_window_elements()[values['photo_selected_action.' + event.split('.')[1]]]
            except KeyError:
                print("Element not found! :(")
            device_obj[values['selected_device']].input_tap(data[1])

            # Update combobox elements afterwards

    window.close()


def gui_manual_case(device_obj):
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
            sg.Checkbox('Pull files from device', default=True, size=(16, 1), key='pull_files', enable_events=True),
            sg.Checkbox('and delete them', default=True, size=(12, 1), key='clear_files')
        ],
        [
            sg.Text('Save Location:', size=(11, 1)),
            sg.InputText(size=(35, 1), key='save_location', enable_events=True),
            sg.FolderBrowse(key='save_location_browse_btn')
        ],
    ]

    layout = [
        [sg.Frame('Test Case', case_frame_layout, font='Any 12', title_color='white')],
        [sg.Frame('After Case', post_case_frame_layout, font='Any 12', title_color='white')]
    ]

    window = sg.Window('Automated Photo/Video Testing', layout,
                       icon=r'.\images\automated-video-testing-header-icon.ico')

    # Event Loop to process "events" and get the "values" of the inputs
    while True:
        event, values = window.read(timeout=100)

        window['duration_spinner'].Update(disabled=values['mode_photos'])

        if event == 'save_location':
            if values["pull_files"]:
                window['capture_case_btn'].Update(disabled=False)
                window['capture_multi_cases_btn'].Update(disabled=False)

        if event == "pull_files":
            window['clear_files'].Update(disabled=not values['pull_files'])
            window['save_location'].Update(disabled=not values['pull_files'])
            window['save_location_browse_btn'].Update(disabled=not values['pull_files'])
            if values['save_location'] == '':  # TODO FIX THIS
                window['capture_case_btn'].Update(disabled=True)
                window['capture_multi_cases_btn'].Update(disabled=True)

        if event == "capture_case_btn":
            device_obj.open_snap_cam()
            # Photos Mode
            if values['mode_photos'] or values['mode_both']:
                shoot_photo(device_obj, values['logs_bool'], values['logs_filter'],
                            "{}/logfile.txt".format(values['save_location']))

            # Videos Mode
            if values['mode_videos'] or values['mode_both']:
                shoot_video(device_obj, values['duration_spinner'], values['logs_bool'], values['logs_filter'],
                            "{}/logfile.txt".format(values['save_location']))

            if values['pull_files']:
                if values['save_location']:
                    pull_camera_files(device_obj, values['save_location'], values['clear_files'])
                else:
                    print("Save Location must be set!")


def disconnect_from_gui(device_obj):
    pass


def loading(secs):  # Only gives fanciness
    for i in range(1, 15 * secs):
        sg.popup_animated(image_source=r'.\images\loading3.gif', message='Loading...', no_titlebar=True,
                          font=('Any', 25), text_color='black',
                          background_color='white',
                          alpha_channel=0.8,
                          )
        time.sleep(0.02)
    sg.popup_animated(image_source=None)


def gui():
    sg.theme('DarkGrey5')  # Add a touch of color

    adb = AdbClient.AdbClient()
    devices_list = adb.list_devices()
    # devices_list = ['asd', 'fs', 'gfd']

    loading(3)

    devices_frame = []
    for num in range(1, 6):
        devices_frame += [sg.Checkbox('', key=f'device_attached.{num}', disabled=True, enable_events=True),
                           sg.InputText(key=f'device_serial.{num}', enable_events=False, size=(15, 1),
                                        disabled=True, default_text=''),
                           sg.InputText(key=f'device_friendly.{num}', enable_events=False, size=(20, 1),
                                        disabled=True),
                           sg.Button('Identify',
                                     button_color=(sg.theme_text_element_background_color(), 'silver'),
                                     key=f'identify_device_btn.{num}',
                                     disabled=True,
                                     enable_events=True),
                           sg.Button('Control',
                                     button_color=(sg.theme_text_element_background_color(), 'silver'),
                                     key=f'ctrl_device_btn.{num}',
                                     disabled=True,
                                     enable_events=True)
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

    logs_frame_layout = [
        [sg.Checkbox('Capture Logs', default=False, size=(10, 1), key='logs_bool', enable_events=True)],
        [sg.Text('Logs Filter:'), sg.InputText(size=(42, 1), key='logs_filter', disabled=True)],
    ]

    # All the stuff inside your window.
    layout = [
        [sg.Image(r'.\images\automated-video-testing-header.png')],
        [sg.Frame('Devices', devices_frame, font='Any 12', title_color='white')],
        [sg.Frame('Settings', device_settings_frame_layout, font='Any 12', title_color='white')],
        [sg.Frame('Logs', logs_frame_layout, font='Any 12', title_color='white')],
        [
            sg.Button('Exit', size=(6, 2)),
            sg.Button('Capture Cases (Manual)', size=(25, 2), key='capture_auto_btn', disabled=True),
            sg.Button('Capture Cases (Automated)', size=(25, 2), key='capture_manual_btn', disabled=True)],
        [sg.Text('_' * 75)],
        # [sg.Frame('Output', [[sg.Output(size=(70, 8))]], font='Any 12', title_color='white')],
        [sg.Text('App Version: {}'.format(APP_VERSION), size=(65, 1), justification="right")]
    ]

    # Create the Window
    window = sg.Window('Automated Photo/Video Testing', layout,
                       icon=r'.\images\automated-video-testing-header-icon.ico')
    device = {}  # List to store devices objects

    # Event Loop to process "events" and get the "values" of the inputs
    while True:
        event, values = window.read(timeout=100) #
        devices_list = adb.list_devices()

        if event == sg.WIN_CLOSED or event == 'Exit':  # if user closes window or clicks cancel
            break

        # print('Data: ', values)  # Debugging
        # print('Event: ', event)  # Debugging
        # print('ADB List Devices', devices_list)  # Debugging
        # print('Devices objects: ', device)

        try:
            devices_list_old
        except NameError:
            devices_list_old = []

        try:
            if len(devices_list) > len(devices_list_old):  # If New device found
                diff_device = [str(s) for s in (set(devices_list_old) ^ set(devices_list))][0]
                print("Found new device!!! -> ", diff_device)

                # window['devices'].update(values=devices_list)
                for num in range(1, 6):
                    if values[f'device_serial.{num}'] == diff_device or values[f'device_serial.{num}'] == '':
                        window[f'device_attached.{num}'].Update(disabled=False)
                        window[f'device_serial.{num}'].Update(diff_device)
                        break


            elif len(devices_list) < len(devices_list_old):  # If device is detached
                diff_device = [str(s) for s in (set(devices_list_old) ^ set(devices_list))][0]
                print("Device detached :( -> ", diff_device)

                # window['devices'].update(values=devices_list)
                for num in range(1, 6):
                    if values[f'device_serial.{num}'] == diff_device:
                        window[f'device_attached.{num}'].Update(value=False, disabled=True)
                        window[f'device_friendly.{num}'].Update(disabled=True)

                try:
                    adb.detach_device(diff_device, device[diff_device])
                    del device[diff_device]
                except KeyError:
                    print("Wasn't attached anyway..")

        except UnboundLocalError:
            pass  # devices_list_old not set yet. No worries, will be set on next run of loop.

        devices_list_old = devices_list

        if event == "logs_bool":
            window['logs_filter'].Update(disabled=not values['logs_bool'])

        if event.split('.')[0] == 'device_attached':
            # diff_device = [str(s) for s in (set(devices_values) ^ set(adb.get_attached_devices()))][0]
            diff_device = values[f"device_serial.{event.split('.')[1]}"]

            print('Attached devices list before changing: {}, len: {}'.format(adb.get_attached_devices(),
                                                                               len(adb.get_attached_devices())))  # Debugging
            print('Devices objects list before changes: ', device)

            if values[f"device_attached.{event.split('.')[1]}"]:  # Connect device
                device[diff_device] = Device(adb, diff_device)  # Assign device to object

                for num in range(1, 6):
                    if values[f'device_serial.{num}'] == diff_device or values[f'device_serial.{num}'] == '':
                        # window[f'device_attached.{num}'].Update(disabled=False)
                        # window[f'device_serial.{num}'].Update(diff_device)
                        window[f'device_friendly.{num}'].Update(values[f'device_friendly.{num}'] if values[f'device_friendly.{num}'] else device[diff_device].get_device_model(), disabled=False)
                        window[f'identify_device_btn.{num}'].Update(disabled=False)
                        window[f'ctrl_device_btn.{num}'].Update(disabled=False)
                        break

                print('Added {} to attached devices!'.format(diff_device))

                print('Currently opened app: {}'.format(device[diff_device].get_current_app()))
            else:  # Detach
                adb.detach_device(diff_device, device[diff_device])
                del device[diff_device]

                for num in range(1, 6):
                    if values[f'device_serial.{num}'] == diff_device or values[f'device_serial.{num}'] == '':
                        window[f'device_friendly.{num}'].Update(disabled=True)
                        window[f'identify_device_btn.{num}'].Update(disabled=True)
                        window[f'ctrl_device_btn.{num}'].Update(disabled=True)
                        break

                print('{} was detached!'.format(diff_device))

            print('Attached devices list after changing: {}, len: {}'.format(adb.get_attached_devices(),
                                                                              len(adb.get_attached_devices())))  # Debugging
            print('Devices objects list after changes: ', device)

        if adb.get_attached_devices():
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
                device[device000].identify()
            if event.split('.')[0] == 'ctrl_device_btn':  # Device Control
                print('Opening device control for ' + event.split('.')[1])
                device000 = values[f"device_serial.{event.split('.')[1]}"]
                device[device000].open_device_ctrl()

            # Buttons callbacks
            if event == "camxoverride_btn":
                gui_camxoverride(adb.get_attached_devices(), device)

            if event == "push_file_btn":
                gui_push_file(adb.get_attached_devices(), device)

            if event == "setup_device_btn":
                gui_setup_device(adb.get_attached_devices(), device)
        else:
            # print('No attached devices!')
            window['camxoverride_btn'].Update(disabled=True)
            window['reboot_device_btn'].Update(disabled=True)
            window['push_file_btn'].Update(disabled=True)
            window['setup_device_btn'].Update(disabled=True)
            window['capture_manual_btn'].Update(disabled=True)
            window['capture_auto_btn'].Update(disabled=True)

        if event == 'reboot_device_btn':
            gui_reboot_device(adb.get_attached_devices(), device)

    # Detach attached devices
    for dev in adb.get_attached_devices():
        adb.detach_device(dev, device[dev])

    window.close()
