from actions import *
from device import Device
from AdbClient import AdbClient
import threading
import PySimpleGUI as sg

APP_VERSION = '0.01 Beta'
THREAD_EVENT = '-WATCHDOG-'

def devices_watchdog(window):
    """
    The thread that communicates with the application through the window's events.

    Once a second wakes and sends a new event and associated value to the window
    """
    i = 0
    while True:
        time.sleep(1)
        window.write_event_value(THREAD_EVENT, (threading.current_thread().name, i))      # Data sent is a tuple of thread name and counter
        print('This is cheating from the thread')
        i += 1


def gui_camxoverride(device_obj):
    print("Pulling camxoverridesettings.txt from device...")
    device_obj.pull_file('/vendor/etc/camera/camxoverridesettings.txt', r'.\tmp\camxoverridesettings.txt')

    camxoverride_content = open(r'.\tmp\camxoverridesettings.txt', 'r').read()

    # All the stuff inside your window.
    layout = [[sg.Text('camxoverridesettings.txt:')],
              [sg.Multiline(camxoverride_content, size=(70, 30), key='camxoverride_input')],
              [sg.CloseButton('Close'),
               sg.Button('Save')  # ,
               # sg.Button('Reboot Device', key='reboot_device_btn')
               ]]

    # Create the Window
    window = sg.Window('Edit camxoverridesettings', layout,
                       icon=r'.\images\automated-video-testing-header-icon.ico')

    while True:
        event, values = window.read()

        if event == sg.WIN_CLOSED or event == 'Close':  # if user closes window or clicks cancel
            break

        if event == 'Save':
            print(values)

            print("Saving camxoverridesettings...")

            print("Generating new camxoverridesettings.txt...")
            camxoverride_new = open(r'.\tmp\camxoverridesettings_new.txt', "w")
            camxoverride_new.write(values['camxoverride_input'])
            camxoverride_new.close()

            device_obj.remount()

            print("Pushing new camxoverridesettings.txt file to device...")
            device_obj.push_file(r'.\tmp\camxoverridesettings_new.txt', "/vendor/etc/camera/camxoverridesettings.txt")

        if event == 'reboot_device_btn':
            device_obj.reboot()

    window.close()


def gui_push_tuning(device_obj):  # not tested
    layout = [
        [sg.Text('Tuning File:', size=(11, 1)),
         sg.InputText(size=(35, 1), key='tuning_source_file', enable_events=True),
         sg.FileBrowse()],
        [sg.Button('Push Tuning', button_color=(sg.theme_text_element_background_color(), 'silver'), size=(10, 2),
                   key='push_tuning_file_btn', disabled=True)]
    ]

    # Create the Window
    window = sg.Window('Push Tuning file', layout,
                       icon=r'.\images\automated-video-testing-header-icon.ico')

    while True:
        event, values = window.read()

        if event == sg.WIN_CLOSED or event == 'Close':  # if user closes window or clicks cancel
            break

        if event == 'tuning_source_file':
            window['push_tuning_file_btn'].Update(disabled=False)

        if event == 'Push':
            print(values)

            print("Pushing Tuning to device")

            device_obj.remount()

            print("Pushing new camxoverridesettings.txt file to device...")
            device_obj.push_file(values['tuning_source_file'], "vendor/lib/camera")

    window.close()


def loading(secs): # Only gives fanciness
    for i in range(1, 15 * secs):
        sg.popup_animated(image_source=r'.\images\loading3.gif', message='Loading...', no_titlebar=True,
                          font=('Any', 25), text_color='black',
                          background_color='white',
                          alpha_channel=0.8,
                          )
        time.sleep(0.02)
    sg.popup_animated(image_source=None)


def get_devices(adb, device_frame_layout):
    devices_list = adb.list_devices()


    if devices_list:
        for num, device in enumerate(devices_list):
            device_frame_layout += [sg.Checkbox(f'Device {device}',
                                                # default=True if num == 0 else False,
                                                enable_events=True,
                                                key=f'device{num}',
                                                tooltip='Tick to connect to device, Untick to disconnect'),
                                    sg.Input(default_text=device, visible=False, key=f'device{num}.serial'),
                                    sg.InputText(key=f'device{num}_friendly',
                                                 enable_events=True, size=(20, 1),
                                                 tooltip='Set friendly name for device')],
    else:
        device_frame_layout += [sg.Text('No devices found! :(')],
    return device_frame_layout


def gui():
    sg.theme('DarkGrey5')  # Add a touch of color

    adb = AdbClient()

    loading(1)

    device_frame_layout = get_devices(adb, [])

    # device_frame_layout += [[sg.Button('', size=(10, 3), button_color=('black', sg.theme_background_color()), image_filename=r'.\images\refresh_icon.png', image_size=(50, 50), image_subsample=6, border_width=0, key='refresh_btn')],]

    device_settings_frame_layout = [
        [sg.Button('Edit camxoverridesettings', button_color=(sg.theme_text_element_background_color(), 'silver'),
                   size=(20, 3),
                   key='camxoverride_btn',
                   disabled=True,
                   tooltip='Edit or view camxoverridesettings any connected device'),
         sg.Button('Reboot Device', button_color=(sg.theme_text_element_background_color(), 'silver'),
                   size=(12, 3),
                   key='reboot_device_btn',
                   disabled=True,
                   tooltip='Reboot devices immediately'),
         sg.Button('Push Tuning', button_color=(sg.theme_text_element_background_color(), 'silver'),
                   size=(12, 3),
                   key='push_tuning_btn',
                   disabled=True)],
    ]

    logs_frame_layout = [
        [sg.Checkbox('Capture Logs', default=False, size=(10, 1), key='logs_bool', enable_events=True)],
        [sg.Text('Logs Filter:'), sg.InputText(size=(42, 1), key='logs_filter', disabled=True)],
    ]

    case_frame_layout = [
        [sg.Radio('Photos', "MODE", default=True, key='mode_photos', enable_events=True),
         sg.Radio('Videos', "MODE", key='mode_videos', enable_events=True),
         sg.Radio('Both', "MODE", key='mode_both', enable_events=True),
         sg.Spin([i for i in range(5, 60)], initial_value=10, key='duration_spinner', disabled=True),
         sg.Text('Video Duration (secs)')],
    ]

    post_case_frame_layout = [
        [sg.Checkbox('Pull files from device', default=True, size=(16, 1), key='pull_files', enable_events=True),
         sg.Checkbox('and delete them', default=True, size=(12, 1), key='clear_files')],
        [sg.Text('Save Location:', size=(11, 1)), sg.InputText(size=(35, 1), key='save_location', enable_events=True),
         sg.FolderBrowse(key='save_location_browse_btn')],
    ]

    # All the stuff inside your window.
    layout = [[sg.Image(r'.\images\automated-video-testing-header.png')],
              [sg.Frame('Devices', device_frame_layout, font='Any 12', title_color='white'),
               sg.Frame('Settings', device_settings_frame_layout, font='Any 12', title_color='white')],
              [sg.Frame('Logs', logs_frame_layout, font='Any 12', title_color='white')],
              [sg.Frame('Test Case', case_frame_layout, font='Any 12', title_color='white')],
              [sg.Frame('After Case', post_case_frame_layout, font='Any 12', title_color='white')],
              [sg.Button('Exit', size=(6, 2)),
               sg.Button('Capture Case', size=(12, 2), key='capture_case_btn', disabled=True),
               sg.Button('Capture Cases (Advanced)', size=(20, 2), key='capture_multi_cases_btn', disabled=True)],
              [sg.Text('_' * 107)],
              [sg.Text('Application Logs', size=(70, 1))],
              # [sg.Output(size=(105, 15))],
              [sg.Text('App Version: {}'.format(APP_VERSION), size=(25, 1)), sg.Button(button_text='Test This', key='testtt')]
              ]

    # Create the Window
    window = sg.Window('Automated Photo/Video Testing', layout,
                       icon=r'.\images\automated-video-testing-header-icon.ico')
    device = []  # List to store devices objects
    is_connected = False

    # Event Loop to process "events" and get the "values" of the inputs
    while True:
        event, values = window.read()
        devices_list = adb.list_devices()


        if event == 'testtt':
            device_frame_layout = device_frame_layout[:-1]
            window.FindElement('device0').update('')
            device_frame_layout = []
            event, values = window.read()
            print(device_frame_layout)

        if event == sg.WIN_CLOSED or event == 'Exit':  # if user closes window or clicks cancel
            break
        print('Data: ', values)  # Debugging
        print('Event: ', event)  # Debugging
        print('ADB List Devices', devices_list)  # Debugging

        if event == "logs_bool":
            window['logs_filter'].Update(disabled=not values['logs_bool'])

        if event == "pull_files":
            window['clear_files'].Update(disabled=not values['pull_files'])
            window['save_location'].Update(disabled=not values['pull_files'])
            window['save_location_browse_btn'].Update(disabled=not values['pull_files'])
            if values['save_location'] == '':  ## TODO FIX THIS
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
            window['push_tuning_btn'].Update(disabled=True)

        if devices_list:
            for d_num, device_serial in enumerate(devices_list):
                if event == 'device{}'.format(d_num):
                    if values['device{}'.format(d_num)]:  # If Ticked
                        device.append(Device(adb.client, device_serial))  # Assign device to object
                        is_connected = True
                    else:  # If unticked
                        # del device[d_num]
                        print('Unticked!')


                print('device{}'.format(d_num))  # TODO FIX THIS


        if is_connected:
            window['camxoverride_btn'].Update(disabled=False)
            window['reboot_device_btn'].Update(disabled=False)
            window['push_tuning_btn'].Update(disabled=False)
            if event == "pull_files":
                if values['save_location'] != "":
                    window['capture_case_btn'].Update(disabled=False)
                    window['capture_multi_cases_btn'].Update(disabled=False)

        if event == 'reboot_device_btn':
            device.reboot()

        window['duration_spinner'].Update(disabled=values['mode_photos'])

        if event == "capture_case_btn" or event == "camxoverride_btn" or event == 'push_tuning_btn':
            if is_connected:
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
                    gui_camxoverride(device)

                if event == "push_tuning_btn":
                    gui_push_tuning(device)



    window.close()
