from actions import *
from device import Device, list_devices
import PySimpleGUI as sg
import time

def gui_camxoverride(device_obj):

    device_obj.pull_file('/vendor/etc/camera/camxoverridesettings.txt', r'.\camxoverridesettings.txt')

    file_content = open('camxoverridesettings.txt', 'r').read()

    # All the stuff inside your window.
    layout = [[sg.Text('camxoverridesettings.txt:')],
                 [sg.Multiline(file_content, size=(70, 30))],
                 [sg.Cancel(), sg.Button('Save')]]

    # Create the Window
    window = sg.Window('Edit camxoverridesettings', layout,
                       icon=r'.\images\automated-video-testing-header-icon.ico')

    while True:
        event, values = window.read()

        if event == sg.WIN_CLOSED or event == 'Cancel':  # if user closes window or clicks cancel
            break

        if event == 'Save':
            print("Save camxoverridesettings")

    window.close()

def gui():
    app_version = '0.01 Beta'
    sg.theme('DarkGrey5')  # Add a touch of color

    device_frame_layout = [
        [sg.Listbox(values=list_devices(), size=(30, 3), key='device'),
         sg.Button('', size=(10, 3), button_color=('black', sg.theme_background_color()),
                   image_filename=r'.\images\refresh_icon.png', image_size=(50, 50), image_subsample=6, border_width=0,
                   key='refresh_btn'),
         sg.Button('1. Connect', button_color=(sg.theme_text_element_background_color(), 'silver'), size=(12, 3), key='connect_btn')],
    ]

    device_settings_frame_layout = [
        [sg.Button('Edit camxoverride', button_color=(sg.theme_text_element_background_color(), 'silver'), size=(20, 3),
                   key='camxoverride_btn')],
    ]

    logs_frame_layout = [
        [sg.Checkbox('Capture Logs', default=True, size=(10, 1), key='logs_bool')],
        [sg.Text('Logs Filter:'), sg.InputText(size=(42, 1), key='logs_filter')],
    ]

    case_frame_layout = [
        [sg.Radio('Photos', "MODE", default=True, key='mode_photos', enable_events=True),
        sg.Radio('Videos', "MODE", key='mode_videos', enable_events=True),
        sg.Radio('Both', "MODE", key='mode_both', enable_events=True),
        sg.Spin([i for i in range(5, 60)], initial_value=10, key='duration_spinner', disabled=True),
        sg.Text('Video Duration (secs)')],
    ]

    post_case_frame_layout = [
        [sg.Checkbox('Pull files from device', default=True, size=(16, 1), key='pull_files'),
        sg.Checkbox('and delete them', default=True, size=(12, 1), key='clear_files')],
        [sg.Text('Save Location:', size=(11, 1)), sg.InputText(size=(35, 1), key='save_location'), sg.FolderBrowse()],
    ]

    # All the stuff inside your window.
    layout = [[sg.Image(r'.\images\automated-video-testing-header.png')],
              [sg.Frame('Device', device_frame_layout, font='Any 12', title_color='white'),
               sg.Frame('Settings', device_settings_frame_layout, font='Any 12', title_color='white')],
              [sg.Frame('Logs', logs_frame_layout, font='Any 12', title_color='white')],
              [sg.Frame('Test Case', case_frame_layout, font='Any 12', title_color='white'),
               sg.Frame('After Case', post_case_frame_layout, font='Any 12', title_color='white')],
              [sg.Button('Exit', size=(6, 2)), sg.Button('Capture Case', size=(20, 2), key='capture_case_btn')],
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

        if event == "refresh_btn":
            window['device'].update(values=list_devices())

        if event == "connect_btn":
            # Assign device to object
            if values['device']:
                device = Device(values['device'][0])
                device.open_snap_cam()
            else:
                print("First select a device!")

        if event == "capture_case_btn" or event == "camxoverride_btn":
            try:
                device
            except NameError:
                print("First select a device and connect to it!")
            else:
                if event == "capture_case_btn":  # TODO Add error handling here if device was not initialized (Object has not been created)
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

                    if values['pull_files']:
                        pull_camera_files(device, values['save_location'], values['clear_files'])

                if event == "camxoverride_btn":
                    gui_camxoverride(device)

    window.close()


def main():
    # device = Device()

    # shoot_video(device, 5)
    # device.open_snap_cam()
    # device.take_photo()
    # shoot_video(device, 10, True, "Gain:ExpTime", "logfile.txt")
    # device.push_file("tuning/com.qti.tuned.snap_imx476.bin", "vendor/lib/camera")
    # pull_camera_files(device, "tests2", True)

    gui()


if __name__ == "__main__":
    main()
