import os
import PySimpleGUI as sg
from pathlib import Path

import src.constants as constants
from src.app.AutomatedCase import parse_lights_xml_seq


def lights_xml_gui(seq_xml_name):
    data = parse_lights_xml_seq(os.path.join(constants.ROOT_DIR, 'lights_seq', f"{seq_xml_name}.xml"))
    print(
        "Name: ", data[0],
        "\nDesc: ", data[1],
        "\nContents: ", data[2]
    )

    treedata = sg.TreeData()

    for light_temp in data[2].keys():
        treedata.Insert("", f'{light_temp}_key', light_temp, len(data[2][light_temp]))
        for lux in data[2][light_temp]:
            treedata.Insert(f'{light_temp}_key', f'{light_temp}_{lux}', lux, [])

    layout = [
        [
            sg.T('Name: ', size=(9, 1)),
            sg.T(data[0])
        ],
        [
            sg.T('Description: '),
            sg.T(data[1])
        ],
        [
            sg.Tree(data=treedata,
                    headings=['LUX No', ],
                    auto_size_columns=True,
                    num_rows=20,
                    col0_width=40,
                    key='-TREE-',
                    show_expanded=False,
                    enable_events=False),
        ],
    ]

    # Create the Window
    window = sg.Window('Push file file', layout,
                       icon=os.path.join(constants.ROOT_DIR, 'images', 'automated-video-testing-header-icon.ico'))

    while True:
        event, values = window.read()

        if event == sg.WIN_CLOSED or event == 'Close':  # if user closes window or clicks cancel
            break

        print('vals', values)  # Debugging
        print('event', event)  # Debugging



    window.close()
