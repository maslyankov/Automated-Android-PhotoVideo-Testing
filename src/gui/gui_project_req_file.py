import json
import os
import PySimpleGUI as sg

import src.constants as constants
from src.app.utils import convert_dict_to_xml, convert_xml_to_dict
from src.gui.utils_gui import Tree, place
from src.app.Reports import Report

is_excel = False


def gui_project_req_file(proj_req=None, return_val=False):
    global is_excel
    go_templ_btn_clicked = False

    tree = Tree(
        headings=['LUX No', ],
        num_rows=20,
        key='-TREE-', )

    # Lists Data
    test_modules_list = list(constants.IMATEST_TEST_TYPES.keys())
    light_types_list = constants.AVAILABLE_LIGHTS[1] # TODO: pass light num so that we show relevant stuff

    # Parameters
    params_list = ['R_pixel_mean', 'G_pixel_mean', 'B_pixel_mean']
    imatest_params_file = open(os.path.join(constants.DATA_DIR, 'imatest_params.json'))
    imatest_params = json.load(imatest_params_file)

    params_list = list(imatest_params[test_modules_list[0]].keys())

    left_col = [[tree]]

    excel_formats = "".join(f"*.{w} " for w in constants.EXCEL_FILETYPES).rstrip(' ')

    top_left_col = [
        [sg.FileBrowse(
            button_text='Import',
            key='import_btn',
            file_types=(
                ("Proj Req", "*.projreq"),
                ('Microsoft Excel', excel_formats),
            ),
            enable_events=True,
            target='import_btn',
            size=(10, 1)
        )],
        [sg.SaveAs(
            button_text='Export',
            key='export_btn',
            file_types=(("Proj Req", "*.projreq"),),
            enable_events=True,
            target='export_btn',
            size=(10, 1)
        )]
    ]
    top_right_col = [
        [sg.B('Fetch New\nImatest\nParameters', key='update_params_btn', size=(11, 3))]
    ]

    min_max_left = [
        [
            sg.Text('Min: ', size=(4, 1)),
            sg.InputText(key='param_min_value', size=(10, 1))
        ],
        [
            sg.Text('Max: ', size=(4, 1)),
            sg.InputText(key='param_max_value', size=(10, 1))
        ]
    ]
    min_max_right = [
        [sg.B('Add\nMin,Max', key='add_min_max_btn', size=(10, 3))]
    ]

    right_col = [
        [
            sg.Column(top_left_col),
            sg.T(' - - '),
            sg.Column(top_right_col),
        ],
        [sg.HorizontalSeparator()],
        [sg.T('Currently loaded: ', size=(18, 1)),sg.B('Save', key='save_btn', disabled=True, size=(10, 1))],
        [sg.T('New requirements file', key='current_filename_label', size=(30, 1))],
        [sg.HorizontalSeparator()],
        [
            sg.Combo(test_modules_list, key='add_type_value', size=(15, 1), default_value=test_modules_list[0], enable_events=True),
            sg.B('Add Type', key='add_type_btn', size=(10, 1)),
        ],
        [sg.HorizontalSeparator()],
        [
            sg.Combo(light_types_list, key='add_light_temp_value', size=(15, 1), default_value=light_types_list[0]),
            sg.B('Add Temp', key='add_light_temp_btn', size=(10, 1)),
        ],
        [
            sg.Spin([i for i in range(10, 1000)], initial_value=20, key='add_lux_value', size=(15, 1)),
            sg.B('Add LUX', key='add_lux_btn', size=(10, 1)),
        ],
        [sg.HorizontalSeparator()],
        [
            sg.Combo(params_list, key='add_param_value', size=(32, 1), default_value=params_list[0])
        ],
        [
            sg.B('Add Param', key='add_param_btn', size=(30, 1))
        ],
        [
            sg.Column(min_max_left), sg.Column(min_max_right),
        ],
        [sg.HorizontalSeparator()],
        [
            sg.B('/\\', key='mv_up_btn', size=(4, 2)),
            sg.B('\\/', key='mv_down_btn', size=(4, 2)),
            sg.B('X', key='delete_btn', size=(4, 2)),
        ],
        [sg.HorizontalSeparator()],
        [
            sg.B('Expand', key='expand_btn', size=(10, 1)),
            sg.B('Collapse', key='collapse_btn', size=(10, 1)),
            sg.B('Clear', key='clear_btn', size=(6, 1)),
        ],
        [sg.HorizontalSeparator()],
        [
            place(sg.Button('Execute Template!', key='go_templ_btn', visible=False, size=(30, 2)))
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

    done = False
    current_file = None

    while True:
        event, values = window.read(timeout=100)

        if event == sg.WIN_CLOSED or event == 'Close' or event == 'go_templ_btn':  # if user closes window or clicks cancel
            if event == 'go_templ_btn':
                go_templ_btn_clicked = True
            break

        # current = tree.where()
        # curr_sel_test_type = current

        # while(tree.get_text(curr_sel_test_type) not in list(constants.IMATEST_TEST_TYPES.keys())):
        #     curr_sel_test_type = tree.treedata.tree_dict[curr_sel_test_type].parent
        #
        # current_test_type = tree.get_text(curr_sel_test_type)
        #
        # print(f'now at {current_test_type} test type ')

        selected = tree.where()
        selected_text = tree.get_text(selected)

        # This does not work - when file is passed, it does not get seen until an event occurs -> current workaround is timeout
        if not done:
            done = True
            if proj_req is not None:
                print('Proj Req: ', proj_req)
                current_file = import_templ(proj_req, tree)
            if return_val:
                window['go_templ_btn'].Update(visible=True)

        if event == 'add_type_value':
            params_list = list(imatest_params[values['add_type_value']].keys())
            window['add_param_value'].Update(values=params_list)
        elif isinstance(selected_text, str) and selected_text.lower() in list(imatest_params.keys()):
            params_list = list(imatest_params[selected_text.lower()].keys())
            window['add_param_value'].Update(values=params_list)

        print('vals', values)  # Debugging
        print('event', event)  # Debugging

        if event == 'clear_btn':
            if sg.popup_yes_no('Are you sure you want to remove all entries?') == 'Yes':
                tree.delete_all_nodes()

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
                xml = convert_dict_to_xml(dump_dict, 'projreq_file')
                print("Out XML:\n", xml)
                with open(current_file, 'wb') as outfile:
                    outfile.write(xml)

        if event == 'export_btn':
            if values['export_btn'].endswith('.projreq'):
                current_file = os.path.normpath(values['export_btn'])
                dump_dict = tree.dump_tree_dict()
                # open output file for writing
                xml = convert_dict_to_xml(dump_dict, 'projreq_file', bool(current_file))
                print("Out XML:\n", xml)
                with open(current_file, 'wb') as outfile:
                    outfile.write(xml)
            elif values['export_btn'] == '':
                pass
            else:
                sg.popup_error('Wrong file format!')

        if event == 'import_btn':
            # Import file
            if values['import_btn'] == '':
                pass
            else:
                current_file = import_templ(values['import_btn'], tree)

        if event == 'update_params_btn':
            if sg.popup_yes_no('Are you sure you want to refetch params from Imatest?\n'
                               'This will do actual tests and parse their results,\n'
                               'so keep in mind it takes time.') == 'Yes':
                # Parse to file (Update file)
                update_imatest_params()

                # Reload params from file
                imatest_params = json.load(imatest_params_file)

                # window['add_param_value'].Update(values=params_list)

        if current_file is not None:
            window['current_filename_label'].Update(current_file.split(os.path.sep)[-1])
            if not is_excel:
                window['save_btn'].Update(disabled=False)
            else:
                window['save_btn'].Update(disabled=True)
        else:
            window['current_filename_label'].Update('New requirements file')

        if current_file is not None and current_file.endswith('.projreq'):
            window['save_btn'].Update(disabled=False)
        else:
            window['save_btn'].Update(disabled=True)

    window.close()
    if go_templ_btn_clicked:
        return tree.dump_tree_dict()
    else:
        return None


def import_templ(templ_in, tree):
    global is_excel

    if templ_in is not None:
        templ_in = os.path.normpath(templ_in)
        # Check if it is an Excel file
        for ext in constants.EXCEL_FILETYPES:
            if templ_in.endswith(ext):
                print('input file: ', templ_in)
                template_data = Report.parse_excel_template(templ_in)
                is_excel = True
                break
        # Check if it is an .proj_req file
        try:
            template_data
        except NameError:
            if templ_in.endswith('projreq'):
                file_data = convert_xml_to_dict(templ_in)['projreq_file']
                print("file data: ", file_data)
                try:
                    print(f"created {file_data['time_created']}")
                except KeyError:
                    pass
                try:
                    print(f" was last modified {file_data['time_updated']} ")
                except KeyError:
                    pass
                print(f"is \n{file_data['proj_req']}")
                template_data = file_data['proj_req']
                is_excel = False
            else:
                sg.popup_error('Unknown proj_req filetype.')
        # Load file to gui tree
        try:
            template_data
        except NameError:
            pass
        else:
            tree.load_dict(template_data)
            # tree.expand_all()
            return templ_in
    else:
        pass
    return None


def recursive_items(dictionary):
    for key, value in dictionary.items():
        if type(value) is dict:
            yield from recursive_items(value)
        else:
            yield (key, value)


def update_imatest_params():
    report_obj = Report()
    images_dict = {'test_serial': []}
    tests_params = {}
    ini_file = os.path.join(constants.ROOT_DIR, 'images', 'imatest', 'ini_file', 'imatest-v2.ini')

    tests_list = images_dict['test_serial']
    for test_name in constants.IMATEST_TEST_TYPES.keys():
        img_file = os.path.join(constants.ROOT_DIR, 'images', 'imatest', f'{test_name}_example')
        if os.path.exists(img_file+'.jpg'):
            img_file += '.jpg'
        elif os.path.exists(img_file+'.png'):
            img_file += '.png'
        else:
            continue

        new_dict = {
            'analysis_type': test_name,
            'image_files': [img_file]
        }

        tests_list.append(new_dict)

    result = report_obj.analyze_images_parallel(images_dict, ini_file)
    # open output file for writing
    result_out_file = os.path.join(constants.DATA_DIR, 'imatest_all_tests_results.json')
    with open(result_out_file, 'w') as outfile:
        json.dump(result, outfile)

    filter_params = ['build', 'EXIF_results', 'errorID', 'errorMessage', 'errorReport']
    for res_dict in result:
        current_type = None
        for key, value in recursive_items(res_dict):
            if current_type is None:
                if key == 'title':
                    current_type = value.split('_')[0]
            else:
                val_type = type(value).__name__
                if val_type == type(str).__name__ or key in filter_params:
                    # Skip string params
                    continue
                try:
                    tests_params[current_type]
                except KeyError:
                    tests_params[current_type] = {}
                    tests_params[current_type][key] = val_type
                else:
                    tests_params[current_type][key] = val_type

    # open output file for writing
    params_out_file = os.path.join(constants.DATA_DIR, 'imatest_params.json')
    with open(params_out_file, 'w') as outfile:
        json.dump(tests_params, outfile)