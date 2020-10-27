import json
import os
import threading
import time

import PySimpleGUI as sg

import src.constants as constants
from src.app.utils import convert_dict_to_xml, convert_xml_to_dict
from src.gui.utils_gui import Tree, place, collapse, SYMBOL_DOWN, SYMBOL_UP
from src.app.Reports import Report

is_excel = False


def gui_project_req_file(proj_req=None, return_val=False):
    global is_excel
    go_templ_btn_clicked = False
    file_is_new = True

    tree = Tree(
        headings=['LUX No', ],
        num_rows=20,
        key='-TREE-', )

    # Lists Data
    test_modules_list = list(constants.IMATEST_PARALLEL_TEST_TYPES.keys())
    light_types_list = constants.AVAILABLE_LIGHTS[1] # TODO: pass light num so that we show relevant stuff

    # Parameters
    imatest_params_file_location = os.path.join(constants.DATA_DIR, 'imatest_params.json')
    imatest_params_file = open(imatest_params_file_location)
    imatest_params = json.load(imatest_params_file)

    params_list = list(imatest_params[test_modules_list[0]].keys())

    left_col = [[tree]]

    excel_formats = "".join(f"*.{w} " for w in constants.EXCEL_FILETYPES).rstrip(' ')

    # Collapsables
    opened_impexp, opened_tt, opened_temp, opened_lux, opened_param = False, False, False, False, False

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

    # ##
    expimp_section = [[
        sg.Column(top_left_col),
        sg.T(' - - '),
        sg.Column(top_right_col),
    ]]

    temp_section = [
        [
            sg.Combo(light_types_list, key='add_light_temp_value', size=(18, 1), pad=(7,2), default_value=light_types_list[0]),
            sg.B('Add Temp', key='add_light_temp_btn', size=(10, 1)),
        ]
    ]

    tt_section = [
        [
            sg.Combo(test_modules_list, key='add_type_value', size=(18, 1), pad=(7, 2),
                     default_value=test_modules_list[0], enable_events=True),
            sg.B('Add Type', key='add_type_btn', size=(10, 1)),
        ]
    ]

    lux_section = [
        [
            sg.Spin([i for i in range(10, 1000)], initial_value=20, key='add_lux_value', size=(19, 1)),
            sg.B('Add LUX', key='add_lux_btn', size=(10, 1)),
        ]
    ]

    right_col = [
        [sg.T('Currently loaded: ', size=(18, 1)), sg.B('Save', key='save_btn', disabled=True, size=(10, 1))],
        [sg.T('New requirements file', key='current_filename_label', size=(30, 1))],
        [sg.HorizontalSeparator()],

            [sg.T(SYMBOL_DOWN if opened_impexp else SYMBOL_UP, enable_events=True, k='-OPEN SEC_IMPEXP-', text_color='yellow'),
             sg.T('Import / Export', enable_events=True, text_color='yellow', k='-OPEN SEC_IMPEXP-TEXT')],
            [collapse(expimp_section, '-SEC_IMPEXP-', visible=opened_temp)],

        [sg.HorizontalSeparator()],
            [sg.T(SYMBOL_DOWN if opened_tt else SYMBOL_UP, enable_events=True, k='-OPEN SEC_TT-', text_color='yellow'),
             sg.T('Test Type', enable_events=True, text_color='yellow', k='-OPEN SEC_TT-TEXT')],
            [collapse(tt_section, '-SEC_TT-', visible=opened_tt)],

            [sg.T(SYMBOL_DOWN if opened_temp else SYMBOL_UP, enable_events=True, k='-OPEN SEC_TEMP-', text_color='yellow'),
             sg.T('Color Temp', enable_events=True, text_color='yellow', k='-OPEN SEC_TEMP-TEXT')],
            [collapse(temp_section, '-SEC_TEMP-', visible=opened_temp)],

            [sg.T(SYMBOL_DOWN if opened_lux else SYMBOL_UP, enable_events=True, k='-OPEN SEC_LUX-', text_color='yellow'),
             sg.T('Lux', enable_events=True, text_color='yellow', k='-OPEN SEC_LUX-TEXT')],
            [collapse(temp_section, '-SEC_LUX-', visible=opened_lux)],

        [sg.HorizontalSeparator()],
        [
            sg.Combo(params_list, key='add_param_value', size=(32, 1), default_value=params_list[0], enable_events=True)
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

        # Sections
        if event.startswith('-OPEN SEC_IMPEXP-'):
            opened_impexp = not opened_impexp
            window['-OPEN SEC_IMPEXP-'].update(SYMBOL_DOWN if opened_temp else SYMBOL_UP)
            window['-SEC_IMPEXP-'].update(visible=opened_impexp)

        if event.startswith('-OPEN SEC_TEMP-'):
            opened_temp = not opened_temp
            window['-OPEN SEC_TEMP-'].update(SYMBOL_DOWN if opened_temp else SYMBOL_UP)
            window['-SEC_TEMP-'].update(visible=opened_temp)

        if event.startswith('-OPEN SEC_LUX-'):
            opened_lux = not opened_lux
            window['-OPEN SEC_LUX-'].update(SYMBOL_DOWN if opened_lux else SYMBOL_UP)
            window['-SEC_LUX-'].update(visible=opened_lux)

        if event == '-TREE-':
            # When selecting item check for what test type it is in
            current = tree.where()
            curr_sel_test_type = current

            while(curr_sel_test_type and tree.get_text(curr_sel_test_type) != '' and str(tree.get_text(curr_sel_test_type)).lower() not in list(constants.IMATEST_PARALLEL_TEST_TYPES.keys())):
                curr_sel_test_type = tree.treedata.tree_dict[curr_sel_test_type].parent
                print(tree.get_text(curr_sel_test_type))

            try:
                current_test_type
            except NameError:
                current_test_type = str(tree.get_text(curr_sel_test_type)).lower()
                # Update list accordingly
                params_list = list(imatest_params[current_test_type].keys())
                window['add_param_value'].Update(params_list[0], values=params_list)
                print(f'now at {current_test_type} test type ')
            else:
                if str(tree.get_text(curr_sel_test_type)).lower() != current_test_type:
                    current_test_type = str(tree.get_text(curr_sel_test_type)).lower()
                    # Update list accordingly
                    if current_test_type == 'root':
                        continue
                    params_list = list(imatest_params[current_test_type].keys())
                    window['add_param_value'].Update(params_list[0], values=params_list)
                    print(f'now at {current_test_type} test type ')

        selected = tree.where()
        selected_text = tree.get_text(selected)

        # This does not work - when file is passed, it does not get seen until an event occurs -> current workaround is timeout
        if not done:
            done = True
            if proj_req is not None:
                print('Proj Req: ', proj_req)
                current_file = import_templ(proj_req, tree)
                return_val = True
                if current_file is not None:
                    file_is_new = False
            if return_val:
                window['go_templ_btn'].Update(visible=True)

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

        if event == 'delete_btn':
            print(f"Delete {tree.get_text(values['-TREE-'][0])}")
            print("Action was successful: ", tree.delete_node(values["-TREE-"][0]))

        if event == 'expand_btn':
            tree.expand_all()
            print('expanding nodes')

        if event == 'collapse_btn':
            tree.collapse_all()
            print('expanding nodes')

        if event == 'update_params_btn':
            if sg.popup_yes_no('Are you sure you want to refetch params from Imatest?\n'
                               'This will do actual tests and parse their results,\n'
                               'so keep in mind it takes some time.') == 'Yes':
                sg.popup_auto_close("Loading... Please wait.", non_blocking=True, no_titlebar=True)

                # Save stuff just in case
                if current_file is not None:
                    dump_dict = tree.dump_tree_dict()
                    # open output file for writing
                    xml = convert_dict_to_xml(dump_dict, 'projreq_file')
                    print("Out XML:\n", xml)
                    with open(current_file, 'wb') as outfile:
                        outfile.write(xml)

                # Parse to file (Update file)
                Report.update_imatest_params()

                # Reload params from file
                imatest_params_file = open(imatest_params_file_location)
                imatest_params = json.load(imatest_params_file)

                sg.popup_ok('All Imatest parameters were dumped successfully!')

        if event == 'import_btn':
            file_is_new = False
            # Import file
            if values['import_btn'] == '':
                pass
            else:
                current_file = import_templ(values['import_btn'], tree)

        if event == 'save_btn':
            if current_file is not None:
                dump_dict = tree.dump_tree_dict()
                # open output file for writing
                xml = convert_dict_to_xml(dump_dict, 'projreq_file', file_is_new)
                print("Out XML:\n", xml)
                with open(current_file, 'wb') as outfile:
                    outfile.write(xml)

        if event == 'export_btn':
            if values['export_btn'].endswith('.projreq'):
                current_file = os.path.normpath(values['export_btn'])
                dump_dict = tree.dump_tree_dict()
                # open output file for writing
                xml = convert_dict_to_xml(dump_dict, 'projreq_file', file_is_new)
                print("Out XML:\n", xml)
                with open(current_file, 'wb') as outfile:
                    outfile.write(xml)
            elif values['export_btn'] == '':
                pass
            else:
                sg.popup_error('Wrong file format!')

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