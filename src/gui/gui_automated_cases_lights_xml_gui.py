import os
import PySimpleGUI as sg
from pathlib import Path

import src.constants as constants
from src.app.AutomatedCase import parse_lights_xml_seq


def get_prev_item(dict, item):
    for i, v in enumerate(dict):
        if v == item:
            try:
                return list(dict)[i - 1]
            except IndexError:
                return None


def get_next_item(dict, item):
    for i, v in enumerate(dict):
        if v == item:
            try:
                return list(dict)[i + 1]
            except IndexError:
                return None


def lights_xml_gui(seq_xml_name):
    data = parse_lights_xml_seq(os.path.join(constants.ROOT_DIR, 'lights_seq', f"{seq_xml_name}.xml"))
    print(
        "Name: ", data[0],
        "\nDesc: ", data[1],
        "\nContents: ", data[2]
    )

    treedata = sg.TreeData()

    for light_temp in data[2].keys():
        treedata.Insert("", f'{light_temp}_key_temp', light_temp, len(data[2][light_temp]))
        for lux in data[2][light_temp]:
            treedata.Insert(f'{light_temp}_key_temp', f'{light_temp}_{lux}_lux', lux, [])

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
        [
            sg.Combo(['D65', 'D75', 'TL84', 'INCA'], key='add_temp_value'),
            sg.B('Add Color Temp', key='add_temp_btn'),
            sg.Spin([i for i in range(10, 1000)], initial_value=20, key='add_lux_value'),
            sg.B('Add LUX', key='add_lux_btn'),
            sg.B('/\\', key='mv_up_btn'),
            sg.B('\\/', key='mv_down_btn'),
            sg.B('X', key='delete_btn'),
        ]
    ]

    # Create the Window
    window = sg.Window('Push file file', layout,
                       icon=os.path.join(constants.ROOT_DIR, 'images', 'automated-video-testing-header-icon.ico'))
    num = 1
    while True:
        event, values = window.read()

        if event == sg.WIN_CLOSED or event == 'Close':  # if user closes window or clicks cancel
            break

        print('vals', values)  # Debugging
        print('event', event)  # Debugging

        if event == 'add_temp_btn':
            treedata.Insert("", f"{values['add_temp_value']}_{num}_key_temp", values['add_temp_value'], [])
            window['-TREE-'].Update(values=treedata)
            print(treedata, type(treedata))
            print(values['-TREE-'])
            num += 1
            print(treedata.tree_dict)

        if event == 'add_lux_btn':
            if values["-TREE-"] != '':
                treedata.Insert(values['-TREE-'][0], f"{values['-TREE-'][0]}_values['add_lux_value']_{num}_key_lux", values['add_lux_value'], [])
                window['-TREE-'].Update(values=treedata)
                print(treedata, type(treedata))
                print(values['-TREE-'][0])
                num += 1
                print(treedata.tree_dict)
            else:
                print('Select temp first')

        if event == 'mv_up_btn':
            print(f'Move up {values["-TREE-"]}')
            foodict = {k: v for k, v in treedata.tree_dict.items() if k.endswith('_temp')}
            prev = get_prev_item(foodict, values["-TREE-"][0])
            if prev is not None and values["-TREE-"][0] != '':
                print('prev: ', prev)
                treedata.move(values["-TREE-"][0], prev)
                window['-TREE-'].Update(values=treedata)

        if event == 'mv_down_btn':
            print(f'Move down {values["-TREE-"]}')
            foodict = {k: v for k, v in treedata.tree_dict.items() if k.endswith('_temp')}
            print('data: ', foodict)
            next = get_next_item(foodict, values["-TREE-"][0])
            if next is not None and values["-TREE-"][0] != '':
                print('next: ', next)
                treedata.move(values["-TREE-"][0], next)
                window['-TREE-'].Update(values=treedata)

        if event == 'delete_btn':
            print(f'Delete {values["-TREE-"]}')
            print("Action was successful: ", treedata.delete(values["-TREE-"][0]))
            window['-TREE-'].Update(values=treedata)
        print('vals: ', values)

    window.close()
