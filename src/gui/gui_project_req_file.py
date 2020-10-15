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

    # Lists Data
    test_modules_list = ['SFR', 'SFR Plus', 'eSFR', 'Gamma']
    light_types_list = ['D65', 'D75', 'TL84', 'INCA']
    params_list = ['R_pixel_mean', 'G_pixel_mean', 'B_pixel_mean']

    current_file = None
    left_col = [[tree]]

    right_col = [
        [
            sg.Combo(test_modules_list, key='add_type_value', size=(15,1)),
            sg.B('Add Type', key='add_type_btn', size=(10, 1)),
        ],
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

        ],
        [
            sg.Combo(params_list, key='add_param_value', size=(15,1)),
            sg.B('Add Param', key='add_param_btn', size=(10, 1)),
        ],
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
            sg.B('/\\', key='mv_up_btn', size=(4, 2)),
            sg.B('\\/', key='mv_down_btn', size=(4, 2)),
            sg.B('X', key='delete_btn', size=(4, 2)),
        ],
        [sg.HorizontalSeparator()],
        [
            sg.B('Expand', key='expand_btn', size=(12, 1)),
            sg.B('Collapse', key='collapse_btn', size=(12, 1)),
        ],
        [sg.HorizontalSeparator()],
            [sg.T('Currently loaded: ')],
            [sg.T('New requirements file', key='current_filename_label', size=(30, 1))],
            [sg.B('Save', key='save_btn', size=(12, 1))],
        [sg.HorizontalSeparator()],
        [
            sg.FileBrowse(
                button_text='Import',
                key='import_btn',
                file_types=(("Proj Req", "*.projreq"),)
            ),
            sg.SaveAs(
                button_text='Export',
                key='export_btn',
                file_types=(("Proj Req", "*.projreq"),)
            )
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

        if current_file is not None:
            # A file is loaded

            pass
        else:
            window['current_filename_label'].Update('New requirements file')

        if event == 'add_type_btn':
            tree.insert_node('', f"{values['add_type_value']}", values['add_type_value'])

        if event == 'add_param_btn':
            current = tree.where()
            if tree.get_text(values['-TREE-'][0]) == 'params':
                tree.insert_node(current, f"{values['add_param_value']}", values['add_param_value'])
            else:
                print('You can only add params to "params"')

        if event == 'add_light_temp_btn':
            current = tree.where()
            if tree.get_text(values['-TREE-'][0]) in test_modules_list:
                tree.insert_node(current, f"{values['add_light_temp_value']}", values['add_light_temp_value'])
            else:
                print('You can only add light temps test type elements')

        if event == 'add_lux_btn':
            current = tree.where()
            if tree.get_text(values['-TREE-'][0]) in light_types_list:
                new_elem = tree.insert_node(current, values['add_lux_value'], values['add_lux_value'])
                tree.insert_node(new_elem, 'params', 'params')
            else:
                print('Select temp first')

        if event == 'add_min_max_btn':
            current = tree.where()
            curr_parent_val = tree.get_parent_value(current)
            if curr_parent_val == 'params':
                min = tree.insert_node(current, 'min', 'min')
                tree.insert_node(min, values['param_min_value'], values['param_min_value'])
                max = tree.insert_node(current, 'max', 'max')
                tree.insert_node(max, values['param_max_value'], values['param_max_value'])
            else:
                print("Trying to add min,max to invalid place. parent val: ", curr_parent_val)

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

        if event == 'save_btn':
            print(tree.dump_tree())


    window.close()
