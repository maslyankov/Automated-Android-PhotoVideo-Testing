from actions import *
from device import Device
import PySimpleGUI as sg
import time

def gui():
    sg.theme('DarkGrey5')  # Add a touch of color
    # All the stuff inside your window.
    layout = [[sg.Image(r'.\images\automated-video-testing-header.png')],
              [
                  sg.Listbox(values=['Device 1', 'Device 2', 'Device 3'], size=(50, 3)),
                  sg.Radio('Photos', "MODE", default=True), sg.Radio('Videos', "MODE"), sg.Radio('Both', "MODE"),
                  sg.Spin([i for i in range(5, 60)], initial_value=10), sg.Text('Video Duration (secs)')
              ],
              [
                  sg.Checkbox('Capture Logs', default=True, size=(13, 1)),
                  sg.Text('Logs Filter'), sg.InputText(size=(77, 1))
              ],
              [sg.Text('Save Location ', size=(15, 1)), sg.InputText(size=(80, 1)), sg.FolderBrowse()],
              [sg.Button('Cancel', size=(10, 2)), sg.Button('Capture Case', size=(20, 2))],
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
        if event == sg.WIN_CLOSED or event == 'Cancel':  # if user closes window or clicks cancel
            break
        print('Data: ', values)

    window.close()

def main():
    device = Device()

    # shoot_video(device, 5)

    device.open_snap_cam()

    #device.take_photo()

    #shoot_video(device, 10, True, "Gain:ExpTime", "logfile.txt")

    #device.push_file("tuning/com.qti.tuned.snap_imx476.bin", "vendor/lib/camera")

    #time.sleep(1)
    #pull_camera_files(device, "tests2", True)

    gui()




if __name__ == "__main__":
    main()
