import json
import os
import PySimpleGUI as sg

import src.constants as constants
from src.app.utils import convert_dict_to_xml, ConvertXMLFileToDict
from src.gui.utils_gui import Tree

def gui_project_req_file(proj_req=None):
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
            sg.Text('',visible=False, key='import_dir'),
            sg.FileBrowse(
                button_text='Import',
                key='import_btn',
                file_types=(("Proj Req", "*.projreq"),),
                enable_events=True,
                target='import_btn'
            ),
            sg.SaveAs(
                button_text='Export',
                key='export_btn',
                file_types=(("Proj Req", "*.projreq"),),
                enable_events=True,
                target='export_btn'
            )
        ],
        [sg.HorizontalSeparator()],
        [sg.T('Currently loaded: ')],
        [sg.T('New requirements file', key='current_filename_label', size=(30, 1))],
        [sg.B('Save', key='save_btn', size=(12, 1))],
        [sg.B('Load Tree', key='load_d_btn', enable_events=True, size=(12, 1))],
        [sg.HorizontalSeparator()],
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
        if event == 'load_d_btn':
            lqlq = False
            tree.load_tree({'': ['', ['1'], 'root', []], '1': ['', ['2'], 'SFR Plus', ['SFR Plus']], '2': ['1', ['3', '4', '5', '6'], 'D65', ['D65']], '3': ['2', ['7'], 20, [20]], '4': ['2', ['8'], 60, [60]], '5': ['2', ['9'], 100, [100]], '6': ['2', ['10'], 200, [200]], '7': ['3', ['11', '12'], 'params', ['params']], '8': ['4', ['13', '14'], 'params', ['params']], '9': ['5', [], 'params', ['params']], '10': ['6', [], 'params', ['params']], '11': ['7', ['15', '17'], 'G_pixel_mean', ['G_pixel_mean']], '12': ['7', ['19', '21'], 'B_pixel_mean', ['B_pixel_mean']], '13': ['8', ['23', '25'], 'B_pixel_mean', ['B_pixel_mean']], '14': ['8', ['27', '29'], 'R_pixel_mean', ['R_pixel_mean']], '15': ['11', ['16'], 'min', ['param-val']], '16': ['15', [], '12', ['12']], '17': ['11', ['18'], 'max', ['param-val']], '18': ['17', [], '21', ['21']], '19': ['12', ['20'], 'min', ['param-val']], '20': ['19', [], '12', ['12']], '21': ['12', ['22'], 'max', ['param-val']], '22': ['21', [], '21', ['21']], '23': ['13', ['24'], 'min', ['param-val']], '24': ['23', [], '2', ['2']], '25': ['13', ['26'], 'max', ['param-val']], '26': ['25', [], '23', ['23']], '27': ['14', ['28'], 'min', ['param-val']], '28': ['27', [], '2', ['2']], '29': ['14', ['30'], 'max', ['param-val']], '30': ['29', [], '23', ['23']]})

        if event == sg.WIN_CLOSED or event == 'Close':  # if user closes window or clicks cancel
            break

        print('vals', values)  # Debugging
        print('event', event)  # Debugging

        if values['import_btn'] != '':
            current_file = os.path.normpath(values['import_btn'])

        if current_file is not None:
            window['current_filename_label'].Update(current_file.split(os.path.sep)[-1])
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
                min = tree.insert_node(current, 'min', 'param-val')
                tree.insert_node(min, values['param_min_value'], values['param_min_value'])
                max = tree.insert_node(current, 'max', 'param-val')
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
            if current_file is not None:
                dump_dict = tree.dump_tree_dict()
                # open output file for writing
                with open(current_file, 'w') as outfile:
                    json.dump(dump_dict, outfile)
                print('Saved this:\n', dump_dict)

        if event == 'export_btn':
            if values['export_btn'].endswith('.projreq'):
                dump_dict = tree.dump_tree_dict()
                # open output file for writing
                # ET.ElementTree(tree_root).write(values['export_btn'])
                xml = convert_dict_to_xml(dump_dict, 'projreq_file')
                print("Out XML:\n", xml)
                with open(values['export_btn'], 'wb') as outfile:
                    outfile.write(xml)
            else:
                sg.popup_error('Wrong file format!')

        if event == 'import_btn':
            # Import file
            if values['import_btn'].endswith('.projreq'):
                dict = ConvertXMLFileToDict(values['import_btn'])['projreq_file']
                print("dict")
                try:
                    print("created {dict['time_created']}")
                except KeyError:
                    pass
                print(f" was last modified {dict['time_updated']} is \n{dict['proj_req']}")
                print(dict)
            else:
                sg.popup_error('Wrong file format or path!')
    window.close()
