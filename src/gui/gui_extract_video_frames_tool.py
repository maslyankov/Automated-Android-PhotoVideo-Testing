import os
import PySimpleGUI as sg

from src.app.utils import extract_video_frame
import src.constants as constants


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
        ],
        [
            sg.Text("Start frame: "),
            sg.Spin([i for i in range(1, 30)], initial_value=1, key='start_frame')
        ],
        [
            sg.Text("Number of frames: "),
            sg.Spin([i for i in range(1, 30)], initial_value=1, key='number_of_frames')
        ],
        [
            sg.Text("Skipped frames: "),
            sg.Spin([i for i in range(0, 30)], initial_value=0, key='skip_frames')
        ],
        [
            sg.Checkbox(text='Save frames to subfolder', default=False, key='frames_subfolder_bool')
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

            for video_file in videofiles_list:
                extract_video_frame(
                    videofile=video_file,
                    start_frame=values['start_frame'],
                    number_of_frames=values['number_of_frames'],
                    skip_frames=values['skip_frames'],
                    subfolder=frames_subfolder
                )
