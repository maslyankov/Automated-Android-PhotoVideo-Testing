import os
import time

import cv2, PySimpleGUI as sg

import src.constants as constants


def gui_cam_tool():
    ports_dict = list_ports()
    cameras = ports_dict[1]
    cameras_list = list(cameras.keys())
    preview_cam = cameras_list[0]

    print("Ports Dict1:", ports_dict)

    layout = [
        [
            sg.Text('Camera: '),
            sg.Combo(cameras_list, default_value=preview_cam, size=(4, 1),
                     key='selected_camera', enable_events=True)]
        ,
        [sg.Image(filename='', key='image')],
    ]

    window = sg.Window('Camera Tool', layout,
                       location=(0, 0),
                       icon=os.path.join(constants.ROOT_DIR, 'images', 'automated-video-testing-header-icon.ico'),
                       grab_anywhere=True)

    cap = cv2.VideoCapture(cameras_list[0])

    while True:
        event, values = window.read(timeout=20)

        if event == sg.WIN_CLOSED:  # if user closes window or clicks cancel
            break

        if event == 'selected_camera':
            preview_cam = values['selected_camera']
            print('Switching preview to camera', )
            cap = cv2.VideoCapture(preview_cam)

        # Update Preview
        window['image'](data=cv2.imencode('.png', cap.read()[1])[1].tobytes())


def list_ports():
    """
    Test the ports and returns a tuple with the available ports and the ones that are working.
    """
    is_working = True
    dev_port = 0
    working_ports = {}
    available_ports = {}
    while is_working:
        camera = cv2.VideoCapture(dev_port)
        if not camera.isOpened():
            is_working = False
            print("Port %s is not working." % dev_port)
        else:
            is_reading, img = camera.read()
            name = "cam"
            w = camera.get(3)
            h = camera.get(4)
            fps = camera.get(cv2.CAP_PROP_FPS)
            if is_reading:
                print("Port %s is working and readable (%s x %s)" % (dev_port, h, w))
                working_ports[dev_port] = {
                    'name': name,
                    'width': w,
                    'height': h,
                    'fps': fps
                }
            else:
                print("Port %s for camera ( %s x %s) is present but not readable." % (dev_port, h, w))
                available_ports[dev_port] = {
                    'name': name,
                    'width': w,
                    'height': h,
                    'fps': fps
                }
        dev_port += 1
    return available_ports, working_ports
