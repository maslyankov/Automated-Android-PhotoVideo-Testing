import os

import PySimpleGUI as sg

from src.code.utils.utils import extract_video_frame
from src import constants
from src.logs import logger


def gui_extract_video_frames_tool():

    layout = [
        [
            sg.Text('Video File/s: '),
            sg.Input(key='videofiles_input'),
            sg.FilesBrowse(
                button_text='Import',
                key='import_btn',
                file_types=(
                    ("Video Files", "*.mp4"),
                ),
                size=(10, 1)
            )
        ],[
            sg.Text("Start frame: "),
            sg.Spin([i for i in range(1, 30)], initial_value=1, key='start_frame', size=(3, 1), pad=((0, 40), 0))
        ,
            sg.Text("Number of frames: "),
            sg.Spin([i for i in range(1, 30)], initial_value=1, key='number_of_frames', size=(3, 1), pad=((0, 40), 0))
        ,
            sg.Text("Skipped frames: "),
            sg.Spin([i for i in range(0, 30)], initial_value=0, key='skip_frames', size=(3, 1), pad=((0, 0), 0))]
        ,
        [
            sg.Checkbox(text='Save frames to subfolder', default=False, key='frames_subfolder_bool', pad=((0, 40), 0)),
            sg.Radio('JPEG', "FORMAT_OUT", default=True, key="jpeg_bool"), sg.Radio('PNG', "FORMAT_OUT", key="png_bool")
        ],
        [
            sg.Button('Extract frames', key='extract_frames_button')
        ]
    ]

    window = sg.Window('Video Frames Extracting Tool', layout,
                       icon=os.path.join(constants.ROOT_DIR, 'images', 'automated-video-testing-header-icon.ico'),
                       grab_anywhere=True)

    while True:
        event, values = window.read()

        if event == sg.WIN_CLOSED:  # if user closes window or clicks cancel
            break

        if event == 'extract_frames_button':
            videofiles_list = values['videofiles_input'].split(';')
            if values['frames_subfolder_bool']:
                frames_subfolder = 'frames'
            else:
                frames_subfolder = False

            if values['jpeg_bool']:
                format_out = "JPEG"
            elif values['png_bool']:
                format_out = "PNG"
            else:
                format_out = None


            # print(values)
            for video_file in videofiles_list:
                print(f"videofile={video_file}, start_frame={values['start_frame']}, number_of_frames={values['number_of_frames']}, skip_frames={values['skip_frames']}, subfolder={frames_subfolder}, out_format={format_out}"
                )
                extract_video_frame(
                    videofile=video_file,
                    start_frame=int(values['start_frame']) if values['start_frame'] else values['start_frame'],
                    number_of_frames=int(values['number_of_frames']) if values['number_of_frames'] else values['number_of_frames'],
                    skip_frames=int(values['skip_frames']) if values['skip_frames'] else values['skip_frames'],
                    subfolder=frames_subfolder,
                    out_format=format_out
                )
            logger.info("Extraction of frames done!")
            sg.popup_ok("Done")
