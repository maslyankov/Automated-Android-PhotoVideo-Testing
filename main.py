from actions import *
from device import Device, list_devices
import PySimpleGUI as sg
import time

def gui():
    sg.theme('DarkGrey5')  # Add a touch of color
    # All the stuff inside your window.
    layout = [[sg.Image(r'.\images\automated-video-testing-header.png')],
              [
                  sg.Listbox(values=list_devices(), size=(50, 3), key='device'),
                  sg.Radio('Photos', "MODE", default=True, key='mode_photos'), sg.Radio('Videos', "MODE", key='mode_videos'), sg.Radio('Both', "MODE", key='mode_both'),
                  sg.Spin([i for i in range(5, 60)], initial_value=10, key='duration_spinner'), sg.Text('Video Duration (secs)')
              ],
              [
                  sg.Checkbox('Capture Logs', default=True, size=(13, 1), key='logs_bool'),
                  sg.Text('Logs Filter'), sg.InputText(size=(77, 1), key='logs_filter')
              ],
              [sg.Text('Save Location ', size=(15, 1)), sg.InputText(size=(80, 1), key='save_location'), sg.FolderBrowse()],
              [sg.Button('Cancel', size=(10, 2)), sg.Button('Connect', size=(20, 2)), sg.Button('Capture Case', size=(20, 2))],
              [sg.Text('_' * 107)],
              [sg.Text('Application Logs', size=(70, 1))],
              [sg.Output(size=(105, 15))]
              ]

    # Create the Window
    window = sg.Window('Automated Photo/Video Testing', layout,
                       icon=r'.\images\automated-video-testing-header-icon.ico')
    # Event Loop to process "events" and get the "values" of the inputs
    while True:
        event, values = window.read()

        if values['mode_photos']:
            window.FindElement('duration_spinner').Update(disabled=True)

        if event == sg.WIN_CLOSED or event == 'Cancel':  # if user closes window or clicks cancel
            break
        print('Data: ', values)
        print("Event: ", event)

        if event == "Connect":
            # Assign device to object
            if values['device']:
                device = Device(values['device'][0])
                device.open_snap_cam()
            else:
                print("First select a device!")

        if event == "Capture Case":
            # Photos Mode
            if values['mode_photos']:
                device.take_photo()

            # Videos Mode
            if values['mode_videos']:
                shoot_video(device, values['duration_spinner'], values['logs_bool'], values['logs_filter'], "logfile.txt")

            # Dual Mode
            if values['mode_both']:
                device.take_photo()
                shoot_video(device, values['duration_spinner'], values['logs_bool'], values['logs_filter'], "logfile.txt")

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
