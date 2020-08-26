from actions import *
from device import Device, list_devices
import PySimpleGUI as sg


def gui_camxoverride(device_obj):
    print("Pulling camxoverridesettings.txt from device...")
    device_obj.pull_file('/vendor/etc/camera/camxoverridesettings.txt', r'.\tmp\camxoverridesettings.txt')

    camxoverride_content = open(r'.\tmp\camxoverridesettings.txt', 'r').read()

    # All the stuff inside your window.
    layout = [[sg.Text('camxoverridesettings.txt:')],
              [sg.Multiline(camxoverride_content, size=(70, 30), key='camxoverride_input')],
              [sg.Cancel(), sg.Button('Save'), sg.Button('Reboot Device', key='reboot_device_btn')]]

    # Create the Window
    window = sg.Window('Edit camxoverridesettings', layout,
                       icon=r'.\images\automated-video-testing-header-icon.ico')

    while True:
        event, values = window.read()

        if event == sg.WIN_CLOSED or event == 'Cancel':  # if user closes window or clicks cancel
            break

        if event == 'Save':
            print(values)

            print("Saving camxoverridesettings...")

            print("Generating new camxoverridesettings.txt...")
            camxoverride_new = open(r'.\tmp\camxoverridesettings_new.txt', "w")
            camxoverride_new.write(values['camxoverride_input'])
            camxoverride_new.close()

            print("Pushing new camxoverridesettings.txt file to device...")
            #device_obj.push_file("camxoverridesettings.txt", "vendor/etc/camera/camxoverridesettings2.txt")
            device_obj.push_file("camxoverridesettings_new.txt", "/vendor/etc/camera/camxoverridesettings2.txt")

        if event == 'reboot_device_btn':
            device_obj.reboot()

    window.close()


def gui():
    app_version = '0.01 Beta'
    sg.theme('DarkGrey5')  # Add a touch of color

    device_frame_layout = [
        [sg.Listbox(values=list_devices(), size=(30, 3), key='device', enable_events=True),
         sg.Button('', size=(10, 3), button_color=('black', sg.theme_background_color()),
                   image_filename=r'.\images\refresh_icon.png', image_size=(50, 50), image_subsample=6, border_width=0,
                   key='refresh_btn')],
    ]

    device_settings_frame_layout = [
        [sg.Button('Edit camxoverridesettings', button_color=(sg.theme_text_element_background_color(), 'silver'), size=(20, 3),
                   key='camxoverride_btn', disabled=True),
         sg.Button('Reboot Device', button_color=(sg.theme_text_element_background_color(), 'silver'), size=(12, 3), key='reboot_device_btn', disabled=True)],
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
        [sg.Text('Save Location:', size=(11, 1)), sg.InputText(size=(35, 1), key='save_location'), sg.FolderBrowse(key='save_location_browse_btn')],
    ]

    # All the stuff inside your window.
    layout = [[sg.Image(r'.\images\automated-video-testing-header.png')],
              [sg.Frame('Device', device_frame_layout, font='Any 12', title_color='white'),
               sg.Frame('Settings', device_settings_frame_layout, font='Any 12', title_color='white')],
              [sg.Frame('Logs', logs_frame_layout, font='Any 12', title_color='white')],
              [sg.Frame('Test Case', case_frame_layout, font='Any 12', title_color='white'),
               sg.Frame('After Case', post_case_frame_layout, font='Any 12', title_color='white')],
              [sg.Button('Exit', size=(6, 2)), sg.Button('Capture Case', size=(12, 2), key='capture_case_btn', disabled=True), sg.Button('Capture Cases (Advanced)', size=(20, 2), key='capture_multi_cases_btn', disabled=True)],
              [sg.Text('_' * 107)],
              [sg.Text('Application Logs', size=(70, 1))],
              # [sg.Output(size=(105, 15))],
              [sg.Text('App Version: {}'.format(app_version), size=(25, 1))]
              ]

    # Create the Window
    window = sg.Window('Automated Photo/Video Testing', layout,
                       icon=r'.\images\automated-video-testing-header-icon.ico')
    # Event Loop to process "events" and get the "values" of the inputs
    while True:
        event, values = window.read()

        try:
            window['duration_spinner'].Update(disabled=values['mode_photos'])
        except (TypeError, AttributeError):
            return

        if event == sg.WIN_CLOSED or event == 'Exit':  # if user closes window or clicks cancel
            break
        print('Data: ', values)  # Debugging
        print('Event: ', event)  # Debugging

        if event == "logs_bool":
            window['logs_filter'].Update(disabled=not values['logs_bool'])

        if event == "pull_files":
            window['clear_files'].Update(disabled=not values['pull_files'])
            window['save_location'].Update(disabled=not values['pull_files'])
            window['save_location_browse_btn'].Update(disabled=not values['pull_files'])

        if event == "refresh_btn":
            print("Refreshing..")
            window['device'].update(values=list_devices())

            window['camxoverride_btn'].Update(disabled=True)
            window['capture_case_btn'].Update(disabled=True)
            window['capture_multi_cases_btn'].Update(disabled=True)
            window['reboot_device_btn'].Update(disabled=True)

        if event == "device":
            # Assign device to object
            if values['device']:
                device = Device(values['device'][0])

                window['camxoverride_btn'].Update(disabled=False)
                window['capture_case_btn'].Update(disabled=False)
                window['capture_multi_cases_btn'].Update(disabled=False)
                window['reboot_device_btn'].Update(disabled=False)
            else:
                print("First select a device!")

        if event == 'reboot_device_btn':
            device.reboot()

        if event == "capture_case_btn" or event == "camxoverride_btn":
            try:
                device
            except NameError:
                print("First select a device and connect to it!")
            else:
                if event == "capture_case_btn":
                    device.open_snap_cam()
                    # Photos Mode
                    if values['mode_photos']:
                        shoot_photo(device, values['logs_bool'], values['logs_filter'],
                                    "{}/logfile.txt".format(values['save_location']))

                    # Videos Mode
                    if values['mode_videos']:
                        shoot_video(device, values['duration_spinner'], values['logs_bool'], values['logs_filter'],
                                    "{}/logfile.txt".format(values['save_location']))

                    # Dual Mode
                    if values['mode_both']:
                        shoot_photo(device, values['logs_bool'], values['logs_filter'],
                                    "{}/logfile.txt".format(values['save_location']))
                        shoot_video(device, values['duration_spinner'], values['logs_bool'], values['logs_filter'],
                                    "{}/logfile.txt".format(values['save_location']))

                    if values['pull_files']: # TODO Add check for save_location if empty
                        if values['save_location']:
                            pull_camera_files(device, values['save_location'], values['clear_files'])
                        else:
                            print("Save Location must be set!")

                if event == "camxoverride_btn":
                    gui_camxoverride(device)

    window.close()
