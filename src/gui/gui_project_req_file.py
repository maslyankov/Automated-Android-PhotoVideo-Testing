import os
import PySimpleGUI as sg

import src.constants as constants
from src.gui.utils_gui import Tree


def gui_project_req_file():
    print('KLQLQLQLQ')
    treedata = sg.TreeData()
    tree = Tree(
        headings=['LUX No', ],
        num_rows=20,
        key='-TREE-', )

    light_types_list = ['D65', 'D75', 'TL84', 'INCA']

    left_col = [[tree]]

    right_col = [
        [
            sg.Combo(['SFR', 'SFR Plus', 'eSFR', 'Gamma'], key='add_type_value', size=(15,1)),
            sg.B('Add Type', key='add_type_btn', size=(10, 1)),
        ],
        [
            sg.Combo(['R_pixel_mean', 'G_pixel_mean', 'B_pixel_mean'], key='add_param_value', size=(15,1)),
            sg.B('Add Param', key='add_param_btn', size=(10, 1)),
        ],
        [sg.HorizontalSeparator()],
        [
            sg.Text('Min: ', size=(12, 1)),
            sg.InputText(key='param_min_value', size=(15, 1))
        ],
        [
            sg.Text('Max: ', size=(12, 1)),
            sg.InputText(key='param_max_value', size=(15, 1))
        ],
        [sg.B('Add Min,Max', key='add_min_max_btn', size=(27, 2))],
        [sg.HorizontalSeparator()],
        [
            sg.Combo(light_types_list, key='add_light_temp_value', size=(15, 1)),
            sg.B('Add Temp', key='add_light_temp_btn', size=(10, 1)),
        ],
        [
            sg.Spin([i for i in range(10, 1000)], initial_value=20, key='add_lux_value', size=(15, 1)),
            sg.B('Add LUX', key='add_lux_btn', size=(10, 1)),
        ],
        [sg.HorizontalSeparator()],
        [
            sg.B('/\\', key='mv_up_btn', size=(4, 2)),
            sg.B('\\/', key='mv_down_btn', size=(4, 2)),
            sg.B('X', key='delete_btn', size=(4, 2)),
        ],
        [sg.HorizontalSeparator()],
        [
            sg.B('Expand', key='expand_btn', size=(12, 1)),
            sg.B('Collapse', key='collapse_btn', size=(12, 1)),
        ]
    ]

    layout = [
        [
            sg.Column(left_col),
            sg.Column(right_col)
        ]
    ]

    # Create the Window
    window = sg.Window('Project Requirements File Tool', layout,
                       icon=os.path.join(constants.ROOT_DIR, 'images', 'automated-video-testing-header-icon.ico'))
    tree.set_window(window)

    while True:
        event, values = window.read()

        if event == sg.WIN_CLOSED or event == 'Close':  # if user closes window or clicks cancel
            break

        print('vals', values)  # Debugging
        print('event', event)  # Debugging

        if event == 'add_type_btn':
            new_type = tree.insert_node('', f"{values['add_type_value']}", values['add_type_value'])

            tree.insert_node(new_type, 'params', values['add_type_value'])
            tree.insert_node(new_type, 'lights', values['add_type_value'])

        if event == 'add_param_btn':
            current = tree.where()
            if tree.get_text(values['-TREE-'][0]) == 'params':
                tree.insert_node(current, f"{values['add_param_value']}", values['add_param_value'])
                tree.select(current)
            else:
                print('You can only add params to "params"')

        if event == 'add_light_temp_btn':
            current = tree.where()
            if tree.get_text(values['-TREE-'][0]) == 'lights':
                tree.insert_node(current, f"{values['add_light_temp_value']}", values['add_light_temp_value'])
                tree.select(current)
            else:
                print('You can only add light temps to "light" elements')

        if event == 'add_lux_btn':
            current = tree.where()
            if tree.get_text(values['-TREE-'][0]) in light_types_list:
                tree.insert_node(current, values['add_lux_value'], values['add_lux_value'])
                tree.select(current)
            else:
                print('Select temp first')

        if event == 'add_min_max_btn':
            current = tree.where()
            #if tree.get_text(values['-TREE-'][0]) in light_types_list:
            min = tree.insert_node(current, 'min', 'min')
            tree.insert_node(min, values['param_min_value'], values['param_min_value'])
            max = tree.insert_node(current, 'max', 'max')
            tree.insert_node(max, values['param_max_value'], values['param_max_value'])

            tree.select(current)
            #else:
            #    print('Select param first')

        if event == 'mv_up_btn':
            print(f'Move up {values["-TREE-"]}')
            tree.move_up()

        if event == 'mv_down_btn':
            print(f'Move down {values["-TREE-"]}')
            tree.move_down()

        if event == 'search_btn':
            print(f'Current key is: {tree.get_value(tree.where())}')

        if event == 'delete_btn':
            print(f"Delete {tree.get_text(values['-TREE-'][0])}")
            print("Action was successful: ", tree.delete_node(values["-TREE-"][0]))

        if event == 'expand_btn':
            tree.expand_all()
            print('expanding nodes')

        if event == 'collapse_btn':
            tree.collapse_all()
            print('expanding nodes')

    window.close()
