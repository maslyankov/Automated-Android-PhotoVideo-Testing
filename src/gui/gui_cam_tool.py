import os
import time
import cv2, PySimpleGUI as sg
import acapture

from src.app.USBCamClient import list_ports
from src import constants


def gui_cam_tool():
    ports_dict = list_ports()
    cameras_list = list(ports_dict.keys())
    preview_cam = ports_dict[cameras_list[-1]]

    print("Ports Dict1:", ports_dict)

    layout = [
        [
            sg.Text('Camera: '),
            sg.Combo(cameras_list, default_value=cameras_list[preview_cam], size=(25, 1),
                     key='selected_camera', enable_events=True),
            sg.Text("Set Resolution: "),
            sg.Input(key='res_width', size=(4, 1)),
            sg.Text("x"),
            sg.Input(key='res_height', size=(4, 1)),
            sg.Button('Set Res', key='set_res_btn'),
            sg.Text('|'),
            sg.Input(key='save_location', size=(10, 1)),
            sg.FolderBrowse(target='save_location'),
            sg.Text('|'),
            sg.Button('Shoot!', key='take_photo_btn')
        ]
        ,
        [sg.Image(filename='', key='image')],
    ]

    window = sg.Window('Camera Tool', layout,
                       #location=(0, 0),
                       icon=os.path.join(constants.ROOT_DIR, 'images', 'automated-video-testing-header-icon.ico'),
                       grab_anywhere=True)

    print('initiating camera')
    cap = cv2.VideoCapture(preview_cam, cv2.CAP_DSHOW)
    #cap = acapture.open(preview_cam)
    get_camera_resolution(cap)
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
            get_camera_resolution(cap)
            # get_max_camera_resolution(cap)

        if event == 'set_res_btn' and values['res_height'] != '' and values['res_width'] != '':
            set_camera_resolution(cap, values['res_width'], values['res_height'])
            print('Now at:')
            get_camera_resolution(cap)

        if event == 'take_photo_btn':
            save_loc = os.path.join(values['save_location'], 'image_out.jpg')
            cam_take_photo(frame, save_loc)

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

def set_camera_resolution(cam, width, height):
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, int(height))
    cam.set(cv2.CAP_PROP_FRAME_WIDTH, int(width))

def cam_take_photo(frame, dest):
    cv2.imwrite(dest, frame)  # save frame as JPEG file