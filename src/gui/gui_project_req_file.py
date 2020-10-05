import os
import PySimpleGUI as sg

import src.constants as constants
from src.gui.utils_gui import Tree

def gui_project_req_file():
    tree = Tree(
        headings=['LUX No', ],
        num_rows=20,
        key='-TREE-', )

    layout = [
        [
            tree
        ],
        [
            sg.Combo(['eSFR', 'D75', 'TL84', 'INCA'], key='add_temp_value'),
            sg.B('Add Color Temp', key='add_temp_btn'),
            sg.Spin([i for i in range(10, 1000)], initial_value=20, key='add_lux_value'),
            sg.B('Add LUX', key='add_lux_btn'),
            sg.B('/\\', key='mv_up_btn'),
            sg.B('\\/', key='mv_down_btn'),
            sg.B('X', key='delete_btn'),
        ]
    ]

    # Create the Window
    window = sg.Window('Project Requirements File Tool', layout,
                       icon=os.path.join(constants.ROOT_DIR, 'images', 'automated-video-testing-header-icon.ico'))

    while True:
        event, values = window.read()

        if event == sg.WIN_CLOSED or event == 'Close':  # if user closes window or clicks cancel
            break

        print('vals', values)  # Debugging
        print('event', event)  # Debugging



    window.close()
