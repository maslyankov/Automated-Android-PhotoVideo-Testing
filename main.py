from actions import *
from device import Device
import PySimpleGUI as sg
import time


def main():
    device = Device()

    # shoot_video(device, 5)

    device.open_snap_cam()

    #device.take_photo()

    #shoot_video(device, 10, True, "Gain:ExpTime", "logfile.txt")

    #device.push_file("tuning/com.qti.tuned.snap_imx476.bin", "vendor/lib/camera")

    #time.sleep(1)
    #pull_camera_files(device, "tests2", True)


    sg.theme('DarkBlue3')  # Add a touch of color
    # All the stuff inside your window.
    layout = [[sg.Text('Automated Photo/Video Testing', size=(50,3))],
              [sg.Listbox(values=['Device 1', 'Device 2', 'Device 3'], size=(40, 6))],
              [sg.Radio('Photos', "MODE", default=True), sg.Radio('Videos', "MODE"), sg.Radio('Both', "MODE")],
              [sg.Checkbox('Capture Logs', default=True)],
              [sg.Text('Logs Filter'), sg.InputText()],
              [sg.Button('Cancel', size=(10, 2)), sg.Button('Capture Case', size=(20, 2))],
              [sg.Text('Application Logs', size=(50, 1))],
              [sg.Multiline('Log', size=(80, 15))]
              ]

    # Create the Window
    window = sg.Window('Window Title', layout)
    # Event Loop to process "events" and get the "values" of the inputs
    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED or event == 'Cancel':  # if user closes window or clicks cancel
            break
        print('Device: ', values[0], "Radio Buttons: " ,values[1], values[2], values[3])

    window.close()


if __name__ == "__main__":
    main()
