import os
import time
import cv2, PySimpleGUI as sg

from src.app.USBCamClient import list_ports
import src.constants as constants


def gui_cam_tool():
    ports_dict = list_ports()
    cameras_list = list(ports_dict.keys())
    preview_cam = ports_dict[cameras_list[0]]

    print("Ports Dict1:", ports_dict)

    layout = [
        [
            sg.Text('Camera: '),
            sg.Combo(cameras_list, default_value=cameras_list[preview_cam], size=(25, 1),
                     key='selected_camera', enable_events=True)]
        ,
        [sg.Image(filename='', key='image')],
    ]

    window = sg.Window('Camera Tool', layout,
                       location=(0, 0),
                       icon=os.path.join(constants.ROOT_DIR, 'images', 'automated-video-testing-header-icon.ico'),
                       grab_anywhere=True)

    cap = cv2.VideoCapture(preview_cam)

    while True:
        event, values = window.read(timeout=20)

        if event == sg.WIN_CLOSED:  # if user closes window or clicks cancel
            break

        if event == 'selected_camera':
            preview_cam = ports_dict[values['selected_camera']]
            print('Switching preview to camera', )
            cap = cv2.VideoCapture(preview_cam)

        # Update Preview
        window['image'](data=cv2.imencode('.png', cap.read()[1])[1].tobytes())
