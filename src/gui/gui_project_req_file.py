import json
import os

import PySimpleGUI as sg

import src.constants as constants
from src.utils.xml_tools import convert_dict_to_xml, convert_xml_to_dict
from src.gui.utils_gui import Tree, place, collapse, SYMBOL_DOWN, SYMBOL_UP
from src.gui.gui_imatest_params_upd import gui_imatest_params_upd
from src.utils.excel_tools import parse_excel_template

is_excel = False


def gui_project_req_file(proj_req=None, proj_req_file=None, return_val=False):
    print('proj req got file: ', proj_req_file)
    current_file = None

    global is_excel
    go_templ_btn_clicked = False
    if proj_req_file is None:
        file_is_new = True
    else:
        file_is_new = False
        current_file = proj_req_file

    tree = Tree(
        headings=['LUX No', ],
        num_rows=20,
        key='-TREE-', column_width=40)

    # Lists Data
    test_modules_list = list(constants.IMATEST_PARALLEL_TEST_TYPES.keys())
    light_types_list = list(constants.KELVINS_TABLE.keys()) # constants.AVAILABLE_LIGHTS[1]  # TODO: pass light num so that we show relevant stuff
    # TODO: Add more lights

    # Parameters
    imatest_params_file_location = os.path.join(constants.DATA_DIR, 'imatest_params.json')
    imatest_params_file = open(imatest_params_file_location)
    imatest_params = json.load(imatest_params_file)

    current_test_type = None
    last_test_type = None

    left_col = [[tree]]

    excel_formats = "".join(f"*.{w} " for w in constants.EXCEL_FILETYPES).rstrip(' ')

    # Collapsables
    opened_impexp, opened_tt, opened_temp, opened_lux, opened_params = False, False, False, False, False

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
        [sg.B('Add\nMin,Max', key='add_min_max_btn', size=(10, 2))]
    ]

    # ##
    expimp_section = [[
        sg.Column(top_left_col),
        sg.T(' - - '),
        sg.Column(top_right_col),
    ]]

    temp_section = [
        [
            sg.Combo(light_types_list, key='add_light_temp_value', size=(18, 1), pad=(7, 2),
                     default_value=light_types_list[0], enable_events=True),
            sg.B('Add Temp', key='add_light_temp_btn', size=(10, 1))
        ],
        [
            sg.T(
                f'{constants.KELVINS_TABLE[light_types_list[0]][0]}K',
                key='add_light_temp_kelvins_label', size=(8, 1)),
            sg.T(
                constants.KELVINS_TABLE[light_types_list[0]][1],
                key='add_light_temp_desc_label', size=(20, 1))
        ]
    ]

    tt_section = [[
        sg.Combo(test_modules_list, key='add_type_value', size=(18, 1), pad=(7, 2),
                 default_value=test_modules_list[0], enable_events=True),
        sg.B('Add Type', key='add_type_btn', size=(10, 1)),
    ]]

    lux_section = [[
        sg.Spin([i for i in range(10, 1000)], initial_value=20, key='add_lux_value', size=(19, 1)),
        sg.B('Add LUX', key='add_lux_btn', size=(10, 1)),
    ]]

    list_restrict_max = ['None'] + list(range(1, 100))
    restrict_left = [
        [
            sg.T('Start Val:', size=(7, 1)),
            sg.Spin(values=list(range(1, 100)), initial_value=1, size=(6, 1), key='restrict_start_val')
        ],
        [
            sg.T('End Val:', size=(7, 1)),
            sg.Spin(values=list_restrict_max, initial_value=list_restrict_max[0], size=(6, 1), key='restrict_end_val')
        ]
    ]
    restrict_right = [
        [sg.B('Add\nRestrictors', size=(8, 2), key='add_restrictors_to_param_btn')]
    ]
    restrict_layout = [[
            sg.Column(restrict_left), sg.Column(restrict_right)
    ]]

    params_restrict_bool = False
    params_section = [
        [
            sg.I(key='params_search_filter', size=(42, 1), pad=(3, 0), enable_events=True),
            sg.Checkbox(text='', default=False, key='params_search_bool', pad=(0, 0), enable_events=True)
        ],
        [
            sg.Listbox(
                values=filter_params(imatest_params, ''),
                key='params_search_list',
                size=(42, 5), pad=(3, 0))
        ],
        [
            sg.B('Add Param', key='add_param_btn', size=(38, 1))
        ],
        [
            sg.Column(min_max_left), sg.Column(min_max_right),
        ],
        [
            sg.Checkbox(text='Use absolute value',
                        default=False, key='params_absolute_bool',
                        enable_events=True, disabled=True)
        ],
        [
            collapse(restrict_layout, '-SUBSEC_RESTRICTS-', visible=params_restrict_bool)
        ]


    ]

    right_col = [
        [sg.T('Currently loaded: ', size=(18, 1)), sg.B('Save', key='save_btn', disabled=True, size=(10, 1))],
        [sg.T('New requirements file', key='current_filename_label', size=(30, 1))],
        [sg.HorizontalSeparator()],

        [sg.T(SYMBOL_DOWN if opened_impexp else SYMBOL_UP, enable_events=True, k='-OPEN SEC_IMPEXP-',
              text_color=constants.PRIMARY_COLOR),
         sg.T('Import / Export', enable_events=True, text_color=constants.PRIMARY_COLOR, k='-OPEN SEC_IMPEXP-TEXT')],
        [collapse(expimp_section, '-SEC_IMPEXP-', visible=opened_temp)],

        [sg.HorizontalSeparator()],

        [sg.T(SYMBOL_DOWN if opened_tt else SYMBOL_UP, enable_events=True, k='-OPEN SEC_TT-',
              text_color=constants.PRIMARY_COLOR),
         sg.T('Test Type', enable_events=True, text_color=constants.PRIMARY_COLOR, k='-OPEN SEC_TT-TEXT')],
        [collapse(tt_section, '-SEC_TT-', visible=opened_tt)],

        [sg.T(SYMBOL_DOWN if opened_temp else SYMBOL_UP, enable_events=True, k='-OPEN SEC_TEMP-',
              text_color=constants.PRIMARY_COLOR),
         sg.T('Color Temp', enable_events=True, text_color=constants.PRIMARY_COLOR, k='-OPEN SEC_TEMP-TEXT')],
        [collapse(temp_section, '-SEC_TEMP-', visible=opened_temp)],

        [sg.T(SYMBOL_DOWN if opened_lux else SYMBOL_UP, enable_events=True, k='-OPEN SEC_LUX-',
              text_color=constants.PRIMARY_COLOR),
         sg.T('Lux', enable_events=True, text_color=constants.PRIMARY_COLOR, k='-OPEN SEC_LUX-TEXT')],
        [collapse(lux_section, '-SEC_LUX-', visible=opened_lux)],

        [sg.T(SYMBOL_DOWN if opened_params else SYMBOL_UP, enable_events=True, k='-OPEN SEC_PARAMS-',
              text_color=constants.PRIMARY_COLOR),
         sg.T('Parameters', enable_events=True, text_color=constants.PRIMARY_COLOR, k='-OPEN SEC_PARAMS-TEXT')],
        [collapse(params_section, '-SEC_PARAMS-', visible=opened_params)],

        [sg.HorizontalSeparator()],
        [
            sg.B('/\\', key='mv_up_btn', size=(3, 2)),
            sg.B('\\/', key='mv_down_btn', size=(3, 2)),
            sg.B('X', key='delete_btn', size=(3, 2)),
            sg.B('EXP', key='expand_btn', size=(4, 2)),
            sg.B('COLL', key='collapse_btn', size=(4, 2)),
            sg.B('CLR', key='clear_btn', size=(4, 2)),
        ],
        [sg.HorizontalSeparator()],
        [
            place(sg.Button('Go!', key='go_templ_btn', visible=False, size=(30, 2)))
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
                       icon=os.path.join(constants.ROOT_DIR, 'images', 'automated-video-testing-header-icon.ico'),
                       return_keyboard_events=True, use_default_focus=False)
    tree.set_window(window)

    done = False
    curr_parent_val = None

    while True:
        event, values = window.read() #timeout=100)

        if event == sg.WIN_CLOSED or event == 'Close' or event == 'go_templ_btn':
            # if user closes window or clicks cancel
            if event == 'go_templ_btn':
                go_templ_btn_clicked = True
            break

        # This does not work - when file is passed,
        # it does not get seen until an event occurs -> current workaround is timeout
        if not done:
            done = True
            if proj_req is not None:
                print('Proj Req: ', proj_req)
                if isinstance(proj_req, dict):
                    current_file = import_templ(proj_req, tree, templ_in_file=proj_req_file)
                else:
                    import_templ(templ_in=proj_req, tree=tree)
                    current_file = proj_req
                return_val = True
                if current_file is not None:
                    file_is_new = False
            if return_val:
                window['go_templ_btn'].Update(visible=True)

        # print('vals', values)  # Debugging
        # print('event', event, type(event))  # Debugging

        # Sections
        if event.startswith('-OPEN SEC_IMPEXP-'):
            opened_impexp = not opened_impexp
            opened_tt, opened_temp, opened_lux, opened_params = False, False, False, False

        if event.startswith('-OPEN SEC_TT-'):
            opened_tt = not opened_tt
            opened_impexp, opened_temp, opened_lux, opened_params = False, False, False, opened_params

        if event.startswith('-OPEN SEC_TEMP-'):
            opened_temp = not opened_temp
            opened_impexp, opened_tt, opened_lux, opened_params = False, False, False, False

        if event.startswith('-OPEN SEC_LUX-'):
            opened_lux = not opened_lux
            opened_impexp, opened_tt, opened_temp, opened_params = False, False, False, False

        if event.startswith('-OPEN SEC_PARAMS-'):
            opened_params = not opened_params
            opened_impexp, opened_tt, opened_temp, opened_lux = False, opened_tt, False, False

        # Update UI elements
        window['-OPEN SEC_IMPEXP-'].update(SYMBOL_DOWN if opened_temp else SYMBOL_UP)
        window['-SEC_IMPEXP-'].update(visible=opened_impexp)

        window['-OPEN SEC_TT-'].update(SYMBOL_DOWN if opened_tt else SYMBOL_UP)
        window['-SEC_TT-'].update(visible=opened_tt)

        window['-OPEN SEC_TEMP-'].update(SYMBOL_DOWN if opened_temp else SYMBOL_UP)
        window['-SEC_TEMP-'].update(visible=opened_temp)

        window['-OPEN SEC_LUX-'].update(SYMBOL_DOWN if opened_lux else SYMBOL_UP)
        window['-SEC_LUX-'].update(visible=opened_lux)

        window['-OPEN SEC_PARAMS-'].update(SYMBOL_DOWN if opened_params else SYMBOL_UP)
        window['-SEC_PARAMS-'].update(visible=opened_params)

        if event == 'add_light_temp_value':
            window['add_light_temp_kelvins_label'].Update(f"{constants.KELVINS_TABLE[values['add_light_temp_value']][0]}K")
            window['add_light_temp_desc_label'].Update(f"{constants.KELVINS_TABLE[values['add_light_temp_value']][1]}")

        if event == '-TREE-':
            # When selecting item check for what test type it is in
            current = tree.where()
            current_text = tree.get_text(current)
            curr_parent_val = tree.get_parent_value(current)
            curr_sel_test_type = current
            # print('curr val: ', tree.get_value(current))
            while (
                    curr_sel_test_type and tree.get_text(curr_sel_test_type) != '' and
                    str(tree.get_text(curr_sel_test_type)).lower()
                    not in list(constants.IMATEST_PARALLEL_TEST_TYPES.keys())):
                curr_sel_test_type = tree.treedata.tree_dict[curr_sel_test_type].parent

            if current_test_type is None:
                current_test_type = str(tree.get_text(curr_sel_test_type)).lower()
                # Update list accordingly
                print(f'now at {current_test_type} test type ')
            else:
                if str(tree.get_text(curr_sel_test_type)).lower() != current_test_type:
                    current_test_type = str(tree.get_text(curr_sel_test_type)).lower()
                    # Update list accordingly
                    if current_test_type == 'root':
                        continue
                    print(f'now at {current_test_type} test type ')

            if current_test_type is not None:
                # print(f'current text: "{current_text}"')
                for paramm, paramm_type in imatest_params[current_test_type].items():
                    # print(f'"{paramm} ({paramm_type})",  ?= , "{current_text}"')

                    if paramm == current_text:
                        print('param found!!!')
                        print('its type is: ', paramm_type)
                        window['-SUBSEC_RESTRICTS-'].Update(visible=paramm_type == 'list')

                        has_abs_val = tree.search(text='absolute_value_bool', mode='Current')
                        if has_abs_val is not None:
                            window['params_absolute_bool'].Update(disabled=False, value=tree.get_text(has_abs_val))
                        else:
                            window['params_absolute_bool'].Update(disabled=False, value=False)
                        break
                    else:
                        window['params_absolute_bool'].Update(disabled=True)
                        window['-SUBSEC_RESTRICTS-'].Update(visible=False)

        if event == 'params_absolute_bool':
            if curr_parent_val == 'params':
                has_abs_val = tree.search(text='absolute_value_bool', mode='Current')
                if has_abs_val is None:
                    absolute_node = tree.insert_node(current, 'absolute_value_bool', 'param-val')
                    tree.insert_node(absolute_node, values['params_absolute_bool'], values['params_absolute_bool'])
                else:
                    tree.set_text(has_abs_val, values['params_absolute_bool'])
            else:
                sg.popup_ok("You can only add absolute bool to the parameter.")

        if event == 'add_restrictors_to_param_btn':
            if curr_parent_val == 'params':
                if values['restrict_end_val'] != 'None' and values['restrict_start_val'] > values['restrict_end_val']:
                    sg.popup_ok('Restriction start value cannot be\nbigger than end value!')
                else:
                    has_start_val = tree.search(text='start_value', mode='Current')
                    if has_start_val is None:
                        start_val_node = tree.insert_node(current, 'start_value', 'param-val')
                        tree.insert_node(start_val_node, values['restrict_start_val'], values['restrict_start_val'])
                    else:
                        tree.set_text(has_start_val, values['restrict_start_val'])

                    if values['restrict_end_val'] != 'None':
                        has_end_val = tree.search(text='end_value', mode='Current')
                        if has_end_val is None:
                            start_val_node = tree.insert_node(current, 'end_value', 'param-val')
                            tree.insert_node(start_val_node, values['restrict_end_val'], values['restrict_end_val'])
                        else:
                            tree.set_text(has_end_val, values['restrict_end_val'])
            else:
                sg.popup_ok("You can only add restrictors to the parameter.")

        if event == 'params_search_filter' or event == 'params_search_bool' or current_test_type != last_test_type:
            ret_vals = filter_params(
                imatest_params,
                values['params_search_filter'],
                current_test_type,
                values['params_search_bool'])
            window['params_search_list'].Update(values=ret_vals)

        if event == 'clear_btn':
            if sg.popup_yes_no('Are you sure you want to remove all entries?') == 'Yes':
                tree.delete_all_nodes()

        if event == 'add_type_btn':
            tree.insert_node('', f"{values['add_type_value']}", values['add_type_value'])

        if event == 'add_param_btn':
            try:
                selected_val = values['params_search_list'][0]
            except IndexError:
                sg.popup_ok('Select parameter first!')
            else:
                try:
                    if tree.get_text(values['-TREE-'][0]) == 'params':
                        parent_id = tree.where()
                        tree.insert_node(current, f"{selected_val}", selected_val)
                        tree.select(parent_id)
                    else:
                        sg.popup_ok('You can only add params to "params"!')
                except IndexError:
                    print('Tree empty.')

        if event == 'add_light_temp_btn':
            try:
                if tree.get_text(values['-TREE-'][0]) in test_modules_list:
                    tree.insert_node(current, f"{values['add_light_temp_value']}", values['add_light_temp_value'])
                else:
                    sg.popup_ok('You can only add light temps to test type elements!')
            except IndexError:
                print('Tree empty.')

        if event == 'add_lux_btn':
            try:
                if tree.get_text(values['-TREE-'][0]) in light_types_list:
                    new_elem = tree.insert_node(current, values['add_lux_value'], values['add_lux_value'])
                    tree.insert_node(new_elem, 'params', 'params')
                else:
                    sg.popup_ok('Select temp first')
            except IndexError:
                print('Tree empty.')

        if event == 'add_min_max_btn':
            if curr_parent_val == 'params':
                parent_id = tree.where()
                has_min = tree.search(text='min', mode='Current')
                if has_min is None:
                    min_node = tree.insert_node(current, 'min', 'param-val')
                    tree.insert_node(min_node, values['param_min_value'], values['param_min_value'])
                else:
                    tree.set_text(has_min, values['param_min_value'])

                has_max = tree.search(text='max', mode='Current')
                if has_max is None:
                    max_node = tree.insert_node(current, 'max', 'param-val')
                    tree.insert_node(max_node, values['param_max_value'], values['param_max_value'])
                else:
                    tree.set_text(has_max, values['param_max_value'])

                tree.select(parent_id)
            else:
                sg.popup_ok("Trying to add min,max to invalid place. \nparent val: ", curr_parent_val)

        if event == 'mv_up_btn':
            print(f'Move up {values["-TREE-"]}')
            tree.move_up()

        if event == 'mv_down_btn':
            print(f'Move down {values["-TREE-"]}')
            tree.move_down()

        if event == 'delete_btn' or event == 'Delete:46':
            try:
                select_next = tree.get_prev_next_of_current()

                print(f"Delete {tree.get_text(values['-TREE-'][0])}")
                print("Action was successful: ", tree.delete_node(values["-TREE-"][0]))

                tree.select(select_next)
            except IndexError:
                print('Trying to delete something that is not there.. :(')

        if event == 'expand_btn':
            tree.expand_all()
            print('expanding nodes')

        if event == 'collapse_btn':
            tree.collapse_all()
            print('expanding nodes')

        if event == 'update_params_btn':
            # Save stuff just in case
            if current_file is not None:
                dump_dict = tree.dump_tree_dict()
                # open output file for writing
                xml = convert_dict_to_xml(dump_dict, 'projreq_file')
                print("Out XML:\n", xml)
                with open(current_file, 'wb') as outfile:
                    outfile.write(xml)

            gui_imatest_params_upd()

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

            elif values['export_btn'] == '':
                current_file = None
            else:
                current_file = os.path.normpath(values['export_btn']) + '.projreq'
                #sg.popup_error('Wrong file format!')

            if current_file is not None:
                dump_dict = tree.dump_tree_dict()
                # open output file for writing
                xml = convert_dict_to_xml(dump_dict, 'projreq_file', file_is_new)
                print("Out XML:\n", xml)
                with open(current_file, 'wb') as outfile:
                    outfile.write(xml)

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

        last_test_type = current_test_type

    window.close()
    if go_templ_btn_clicked:
        return {
            'dict': tree.dump_tree_dict(),
            'projreq_file': current_file
        }
    else:
        return None


def filter_params(imatest_params: dict, fltr: str, current_test_type: str = None, search_everywhere: bool = True):
    out_list = []
    print(f'filter params got: \n{imatest_params}\n, {fltr}\n, {current_test_type}')

    for key, value in imatest_params.items():
        for param in list(value.keys()):
            if fltr != '' and fltr is not None:
                param = param
                fltr = fltr.lower()
                if search_everywhere or current_test_type is None:
                    if fltr in param.lower():
                        out_list.append(f'{key} > {param}')
                elif current_test_type == key and fltr in param.lower():
                    out_list.append(f'{param}')
            elif current_test_type == key:
                out_list.append(f'{param}')
            elif current_test_type is None:
                out_list.append(f'{key} > {param}')
    return out_list


def import_templ(templ_in, tree, templ_in_file=None):
    global is_excel
    print('proj req got file: ', templ_in_file)
    print('proj req got: ', templ_in)
    if templ_in is not None:
        if isinstance(templ_in, str):
            templ_in = os.path.normpath(templ_in)
            # Check if it is an Excel file
            for ext in constants.EXCEL_FILETYPES:
                if templ_in.endswith(ext):
                    print('input file: ', templ_in)
                    templ_in_file = templ_in
                    template_data = parse_excel_template(templ_in)
                    is_excel = True
                    break
            # Check if it is an .proj_req file
            try:
                template_data
            except NameError:
                if templ_in.endswith('projreq'):
                    templ_in_file = templ_in
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
        # Check if it is a dict
        elif isinstance(templ_in, dict):
            template_data = templ_in

        # Load file to gui tree
        try:
            template_data
        except NameError:
            pass
        else:
            tree.load_dict(template_data)
            # tree.expand_all()
            return templ_in_file
    else:
        pass
    return None
