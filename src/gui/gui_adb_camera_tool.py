import os
import PySimpleGUI as sg

from src import constants
from src.logs import logger
from src.gui.utils_gui import collapse, explorer_open_file


def wait_with_msg(time: int, message: str = None, font_size=20, text_color=None):
    for secs in range(time, 0, -1):
        msg = f"Please wait {secs} second{'' if secs == 1 else 's'}..."

        if message:
            msg = f"{message}\n{msg}"

        sg.PopupAutoClose(msg, button_type=sg.POPUP_BUTTONS_NO_BUTTONS,
                          auto_close_duration=1,
                          keep_on_top=True, no_titlebar=True,
                          font=f'Any {font_size}' if font_size else None, text_color=text_color)


def capture(device_obj, initial_wait_time=2, num_of_images: int = 1, capture_gap: int = 1,
            pull_images: bool=False, pull_dest=None, timer=0, open_in_explorer=True):
    print(f"Timer is {timer}")
    if timer:
        wait_with_msg(timer, "Timer...", font_size=40, text_color="white")

    # Start the video stream
    logger.info("starting camera_tool stream")
    cam_video_stream = device_obj.open_shell("camera_tool --hal-type chi -T")

    logger.info(f"waiting {initial_wait_time} secs initial wait time")
    wait_with_msg(initial_wait_time, "Waiting for AEC to converge...")

    for shot_number in range(1, num_of_images+1):
        logger.info(f"Capturing photo {shot_number}, {num_of_images-shot_number} left")
        wait_with_msg(capture_gap, f"Capturing photo {shot_number}, {num_of_images-shot_number} left")
        device_obj.exec_shell("setprop persist.vendor.camera.snapshot 1")

    # Stop the stream
    logger.info("stopping camera_tool stream")
    device_obj.close_shell(cam_video_stream)

    # Pull images
    if pull_images and pull_dest:
        pulled_images = device_obj.pull_images(pull_dest, clear_folder=True)

    # Open folder and highlight first image
    try:
        if open_in_explorer and pulled_images:
            explorer_open_file(pulled_images[0])
    except NameError:
        pass



def gui_adb_camera_tool(device_obj, attached_devices=None, specific_device=None):
    if specific_device:
        device_obj[specific_device].load_settings_file()
        persist_setting = device_obj[specific_device].get_persist_setting('last_pull_images_save_dest')
    else:
        device_obj[specific_device].load_settings_file()
        persist_setting = device_obj[attached_devices[0]].get_persist_setting('last_pull_images_save_dest')

    select_device_layout = [
        [
            sg.Text('Device: ', size=(9, 1)),
            sg.Combo(attached_devices if attached_devices else [], size=(20, 20),
                     enable_events=True, key='selected_device',
                     default_value=attached_devices[0] if attached_devices else ""),
            sg.Text(text=device_obj[attached_devices[0]].friendly_name if attached_devices else "",
                    key='device-friendly',
                    size=(13, 1),
                    font="Any 18")
        ]
    ]

    layout = [
        [collapse(select_device_layout, 'select_device_layout', not bool(specific_device))],
        [
            sg.T("Save dest:"),
            sg.I(key='save_dest',
                 default_text=persist_setting if persist_setting else ""),
        ],
        [
            sg.T("Timer (in s):"),
            sg.Spin(initial_value=0, values=list(range(0, 200, +5)), key='timer_input'),
        ],
        [
            sg.T("Initial wait time (in s):"),
            sg.Spin(initial_value=2, values=list(range(0, 10)), key='initial_wait_input'),
        ],
        [
            sg.T("Number of shots (for multi shooting):"),
            sg.Spin(initial_value=3, values=list(range(0, 20)), key='num_shots_input'),
            sg.T("Gap between shots (in secs):"),
            sg.Spin(initial_value=1, values=list(range(0, 10)), key='shots_gap_input')
        ],
        [
            sg.Button('Single\nCapture', size=(10, 2), key='single_capture_btn', disabled=False),
            sg.Button('Multi\nCapture', size=(10, 2), key='multi_capture_btn', disabled=False)
        ]
    ]

    # Create the Window
    window = sg.Window('Pull Images', layout,
                       icon=os.path.join(constants.ROOT_DIR, 'images', 'automated-video-testing-header-icon.ico'))

    while True:
        event, values = window.read()

        if event == sg.WIN_CLOSED or event == 'Close':  # if user closes window or clicks cancel
            break

        logger.debug(f"Event: {event}")  # Debugging
        logger.debug(f"Values: {values}")  # Debugging

        curr_device = device_obj[values['selected_device']] if not specific_device else device_obj[specific_device]
        device_images_dir = curr_device.images_save_loc

        if attached_devices and event == 'selected_device':
            window['device-friendly'].Update(curr_device.friendly_name)

            persist_setting = curr_device.get_persist_setting('last_pull_images_save_dest')
            window['dest_folder'].Update(persist_setting)

        if event == 'single_capture_btn':
            capture(device_obj[specific_device], initial_wait_time=int(values['initial_wait_input']),
                    pull_images=True, pull_dest=values['save_dest'], timer=int(values['timer_input']))

        if event == 'multi_capture_btn':
            capture(device_obj[specific_device], initial_wait_time=int(values['initial_wait_input']),
                    num_of_images=values['num_shots_input'], capture_gap=values['shots_gap_input'],
                    pull_images=True, pull_dest=values['save_dest'], timer=int(values['timer_input']))

    window.close()
