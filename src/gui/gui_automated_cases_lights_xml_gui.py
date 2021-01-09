import os
import PySimpleGUI as sg
from pathlib import Path

from src import constants
from src.logs import logger
from src.app.AutomatedCase import parse_lights_xml_seq
from src.gui.utils_gui import Tree


def lights_xml_gui(seq_xml_name):
    treedata = sg.TreeData()
    data = parse_lights_xml_seq(os.path.join(constants.ROOT_DIR, 'lights_seq', f"{seq_xml_name}.xml"))
    logger.debug(
        f"Name: {data[0]} \nDesc: {data[1]} \nContents: {data[2]}"
    )

    for light_temp in data[2].keys():
        treedata.Insert("", f'{light_temp}_key_temp', light_temp, len(data[2][light_temp]))
        for lux in data[2][light_temp]:
            treedata.Insert(f'{light_temp}_key_temp', f'{light_temp}_{lux}_lux', lux, [])

    tree = Tree(
        headings=['LUX No', ],
        num_rows=20,
        key='-TREE-', )

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
            tree,
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

    tree.set_window(window)

    while True:
        event, values = window.read()

        if event == sg.WIN_CLOSED or event == 'Close':  # if user closes window or clicks cancel
            break

        logger.debug(f'vals {values}')  # Debugging
        logger.debug(f'event {event}')  # Debugging

        if event == 'add_temp_btn':
            logger.info("Add temp")

            tree.insert_node('', f"{values['add_temp_value']}", values['add_temp_value'])
            # window['-TREE-'].Update(values=treedata)
            logger.debug(f"treedata - {treedata} is {type(treedata)}")
            logger.debug(values['-TREE-'])
            num += 1
            logger.debug(f"Treedata dict: {treedata.tree_dict}")

        if event == 'add_lux_btn':
            logger.info("Add lux")

            if values["-TREE-"] != '':
                tree.insert_node(values['-TREE-'][0], f"{values['-TREE-'][0]}_{values['add_lux_value']}_key_lux", values['add_lux_value'])
                # window['-TREE-'].Update(values=treedata)
                logger.debug(f"treedata - {treedata} is {type(treedata)}")
                logger.debug(values['-TREE-'][0])
                num += 1
                logger.debug(f"Treedata dict: {treedata.tree_dict}")
            else:
                logger.error('Select temp first')

        if event == 'mv_up_btn':
            logger.info(f'Move up {values["-TREE-"]}')
            tree.move_up()
            # foodict = {k: v for k, v in treedata.tree_dict.items() if k.endswith('_temp')}
            # prev = get_prev_item(foodict, values["-TREE-"][0])
            # if prev is not None and values["-TREE-"][0] != '':
            #     print('prev: ', prev)
            #     treedata.move(values["-TREE-"][0], prev)
            #     window['-TREE-'].Update(values=treedata)

        if event == 'mv_down_btn':
            logger.info(f'Move down {values["-TREE-"]}')
            tree.move_down()
            # foodict = {k: v for k, v in treedata.tree_dict.items() if k.endswith('_temp')}
            # print('data: ', foodict)
            # next = get_next_item(foodict, values["-TREE-"][0])
            # if next is not None and values["-TREE-"][0] != '':
            #     print('next: ', next)
            #     treedata.move(values["-TREE-"][0], next)
            #     window['-TREE-'].Update(values=treedata)

        if event == 'delete_btn':
            logger.info(f'Delete {values["-TREE-"]}')
            logger.info(f"Action was successful: {treedata.delete(values['-TREE-'][0])}")
            window['-TREE-'].Update(values=treedata)

        logger.debug(f'vals: {values}')

    window.close()
