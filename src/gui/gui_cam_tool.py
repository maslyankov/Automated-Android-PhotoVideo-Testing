import os
import time
import cv2, PySimpleGUI as sg
import acapture

from src.app.USBCamClient import list_ports
import src.constants as constants


def gui_cam_tool():
    ports_dict = list_ports()
    cameras_list = list(ports_dict.keys())
    preview_cam = ports_dict[cameras_list[-1]]

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

    print('initiating camera')
    cap = cv2.VideoCapture(preview_cam, cv2.CAP_DSHOW)
    #cap = acapture.open(preview_cam)
    get_max_camera_resolution(cap)
    print('Loading camera')
    while True:
        event, values = window.read(timeout=20)

        if event == sg.WIN_CLOSED:  # if user closes window or clicks cancel
            break

        if event == 'selected_camera':
            preview_cam = ports_dict[values['selected_camera']]
            print('Switching preview to camera', preview_cam)
            cap = cv2.VideoCapture(preview_cam, cv2.CAP_DSHOW)
            #cap = acapture.open(preview_cam)
            get_max_camera_resolution(cap)

        # Update Preview
        is_alive, frame = cap.read()
        # frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        window['image'](data=cv2.imencode('.png', frame)[1].tobytes())


def get_camera_resolution(cam):
    height = cam.get(cv2.CAP_PROP_FRAME_HEIGHT)
    width = cam.get(cv2.CAP_PROP_FRAME_WIDTH)
    print(f'Cam res: {width}x{height}')

def get_max_camera_resolution(cam):
    max = 10000

    height = cam.set(cv2.CAP_PROP_FRAME_HEIGHT, max)
    width = cam.set(cv2.CAP_PROP_FRAME_WIDTH, max)

    get_camera_resolution(cam)
