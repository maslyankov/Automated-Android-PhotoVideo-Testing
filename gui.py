from actions import *
from device import Device
import AdbClient
import threading
import os
from pathlib import Path
import PySimpleGUI as sg

APP_VERSION = '0.01 Beta'
THREAD_EVENT = '-WATCHDOG-'


def devices_watchdog(window): # TODO
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


def gui_camxoverride(connected_devices, device_obj):
    print("Pulling camxoverridesettings.txt from device...")
    device_obj[connected_devices[0]].pull_file('/vendor/etc/camera/camxoverridesettings.txt', r'.\tmp\camxoverridesettings.txt')

    camxoverride_content = open(r'.\tmp\camxoverridesettings.txt', 'r').read()

    # All the stuff inside your window.
    layout = [
        [sg.Combo(connected_devices, size=(20, 20), key='selected_device', default_value=connected_devices[0], enable_events=True)],
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
            device_obj[values['selected_device']].push_file(r'.\tmp\camxoverridesettings_new.txt', "/vendor/etc/camera/camxoverridesettings.txt")


    window.close()


def gui_push_file(connected_devices, device_obj):
    file_destinations = [
        'sdcard/DCIM/',
        'vendor/lib/camera/'
    ]

    layout = [
        [
            sg.Combo(connected_devices, size=(20, 20), key='selected_device', default_value=connected_devices[0]),
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


def gui_reboot_device(connected_devices, device_obj):

    layout = [
        [sg.Combo(connected_devices, size=(20, 20), key='selected_device', default_value=connected_devices[0])],
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

    device_frame_layout = [
        [sg.Listbox(values=devices_list if devices_list else ['No devices found!'], size=(30, 5),
                    key='devices', enable_events=True,
                    select_mode=sg.LISTBOX_SELECT_MODE_MULTIPLE,
                    tooltip='Select to connect to device, Deselect to disconnect')],
    ]

    friendly_names = []
    for num, serial in enumerate(devices_list):
        friendly_names += [sg.InputText(key=f'device_friendly.{serial}', enable_events=False, size=(20, 1),
                                        tooltip=f'Set friendly name for device{num}', disabled=True),
                           sg.Button(f'Identify device {serial}',
                                     button_color=(sg.theme_text_element_background_color(), 'silver'),
                                     key=f'identify_device.{serial}',
                                     disabled=True,
                                     tooltip='Identify connected device',
                                     enable_events=True)
                           ],

    device_settings_frame_layout = [[
         sg.Button('Edit camxoverridesettings', button_color=(sg.theme_text_element_background_color(), 'silver'),
                   size=(20, 3),
                   key='camxoverride_btn',
                   disabled=True,
                   tooltip='Edit or view camxoverridesettings any connected device'),
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

    # All the stuff inside your window.
    layout = [
                  [sg.Image(r'.\images\automated-video-testing-header.png')],
                  [
                      sg.Frame('Devices', device_frame_layout, font='Any 12', title_color='white'),
                      sg.Frame('Friendly Names', friendly_names, font='Any 12', title_color='white')
                  ],
                  [sg.Frame('Settings', device_settings_frame_layout, font='Any 12', title_color='white')],
                  [sg.Frame('Logs', logs_frame_layout, font='Any 12', title_color='white')],
                  [sg.Frame('Test Case', case_frame_layout, font='Any 12', title_color='white')],
                  [sg.Frame('After Case', post_case_frame_layout, font='Any 12', title_color='white')],
                  [
                      sg.Button('Exit', size=(6, 2)),
                      sg.Button('Capture Case', size=(12, 2), key='capture_case_btn', disabled=True),
                      sg.Button('Capture Cases (Advanced)', size=(20, 2), key='capture_multi_cases_btn', disabled=True)],
                  [sg.Text('_' * 75)],
                  # [sg.Frame('Output', [[sg.Output(size=(70, 8))]], font='Any 12', title_color='white')],
                  [sg.Text('App Version: {}'.format(APP_VERSION), size=(65, 1), justification="right")]
              ]

    # Create the Window
    window = sg.Window('Automated Photo/Video Testing', layout,
                       icon=r'.\images\automated-video-testing-header-icon.ico')
    device = {}  # List to store devices objects
    connected_devices = []

    # Event Loop to process "events" and get the "values" of the inputs
    while True:
        event, values = window.read()
        devices_list = adb.list_devices()

        if event == sg.WIN_CLOSED or event == 'Exit':  # if user closes window or clicks cancel
            break

        print('Data: ', values)  # Debugging
        print('Event: ', event)  # Debugging
        print('ADB List Devices', devices_list)  # Debugging
        print('Devices objects: ', device)

        if event == "logs_bool":
            window['logs_filter'].Update(disabled=not values['logs_bool'])

        if event == "pull_files":
            window['clear_files'].Update(disabled=not values['pull_files'])
            window['save_location'].Update(disabled=not values['pull_files'])
            window['save_location_browse_btn'].Update(disabled=not values['pull_files'])
            if values['save_location'] == '':  # TODO FIX THIS
                window['capture_case_btn'].Update(disabled=True)
                window['capture_multi_cases_btn'].Update(disabled=True)

        # TODO FIX THIS
        if event == "save_location" and values['pull_files']:
            if values['save_location'] == "":
                window['capture_case_btn'].Update(disabled=True)
                window['capture_multi_cases_btn'].Update(disabled=True)
        else:
            window['capture_case_btn'].Update(disabled=False)
            window['capture_multi_cases_btn'].Update(disabled=False)
        ############

        if event == 'save_location':
            if values["pull_files"]:
                window['capture_case_btn'].Update(disabled=False)
                window['capture_multi_cases_btn'].Update(disabled=False)

        if event == "refresh_btn":  # TODO MAKE AUTOMATIC
            print("Refreshing..")
            window['device'].update(values=adb.list_devices())

        if event == "refresh_btn" or event == "reboot_device_btn":
            window['camxoverride_btn'].Update(disabled=True)
            window['capture_case_btn'].Update(disabled=True)
            window['capture_multi_cases_btn'].Update(disabled=True)
            window['reboot_device_btn'].Update(disabled=True)
            window['push_file_btn'].Update(disabled=True)

        devices_values = values['devices']

        if event == 'devices':
            diff_device = [str(s) for s in (set(devices_values) ^ set(connected_devices))][0]

            print('Connected devices list before changing: {}, len: {}'.format(connected_devices, len(connected_devices))) # Debugging
            print('Devices objects list before changes: ', device)

            if len(values['devices']) > len(connected_devices) \
                    and diff_device not in connected_devices:  # Connect device
                device[diff_device] = Device(adb.client, diff_device)  # Assign device to object
                connected_devices.append(diff_device)

                window['device_friendly.' + diff_device].Update(disabled=False)
                window['identify_device.' + diff_device].Update(disabled=False)

                print('Added {} to connected devices!'.format(diff_device))

                print('Currently opened app: {}'.format(device[diff_device].get_current_app()))

            elif len(values['devices']) < len(connected_devices) \
                    and diff_device in connected_devices:  # Disconnect
                del device[diff_device]
                print(device)

                connected_devices.remove(diff_device)

                window['device_friendly.' + diff_device].Update(disabled=True)
                window['identify_device.' + diff_device].Update(disabled=True)

                print('{} was disconnected!'.format(diff_device))

            print('Connected devices list after changing: {}, len: {}'.format(connected_devices, len(connected_devices))) # Debugging
            print('Devices objects list after changes: ', device)

        if connected_devices:
            print('A Device is connected!')
            window['camxoverride_btn'].Update(disabled=False)
            window['reboot_device_btn'].Update(disabled=False)
            window['push_file_btn'].Update(disabled=False)
            if event == "pull_files":
                if values['save_location'] != "":
                    window['capture_case_btn'].Update(disabled=False)
                    window['capture_multi_cases_btn'].Update(disabled=False)
            if event.split('.')[0] == 'identify_device': # Identify Buttons
                print('Identifying ' + event.split('.')[1])
                device[event.split('.')[1]].identify()
        else:
            print('No connected devices!')
            window['camxoverride_btn'].Update(disabled=True)
            window['reboot_device_btn'].Update(disabled=True)
            window['push_file_btn'].Update(disabled=True)
            window['capture_case_btn'].Update(disabled=True)
            window['capture_multi_cases_btn'].Update(disabled=True)

        if event == 'reboot_device_btn':
            gui_reboot_device(connected_devices, device)

        window['duration_spinner'].Update(disabled=values['mode_photos'])

        if event == "capture_case_btn" or event == "camxoverride_btn" or event == 'push_file_btn':
            if not connected_devices:
                print("First select a device and connect to it!")
            else:
                if event == "capture_case_btn":
                    device.open_snap_cam()
                    # Photos Mode
                    if values['mode_photos'] or values['mode_both']:
                        shoot_photo(device, values['logs_bool'], values['logs_filter'],
                                    "{}/logfile.txt".format(values['save_location']))

                    # Videos Mode
                    if values['mode_videos'] or values['mode_both']:
                        shoot_video(device, values['duration_spinner'], values['logs_bool'], values['logs_filter'],
                                    "{}/logfile.txt".format(values['save_location']))

                    if values['pull_files']:
                        if values['save_location']:
                            pull_camera_files(device, values['save_location'], values['clear_files'])
                        else:
                            print("Save Location must be set!")

                if event == "camxoverride_btn":
                    gui_camxoverride(connected_devices, device)

                if event == "push_file_btn":
                    gui_push_file(connected_devices, device)

    window.close()
