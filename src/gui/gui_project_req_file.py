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
    test_modules_list = ['SFR', 'SFR Plus', 'eSFR', 'Gamma']
    light_types_list = ['D65', 'D75', 'TL84', 'INCA']
    params_list = ['R_pixel_mean', 'G_pixel_mean', 'B_pixel_mean']


    left_col = [[tree]]

    excel_formats = "".join(f"*.{w} " for w in constants.EXCEL_FILETYPES).rstrip(' ')
    right_col = [
        [
            sg.Text('', visible=False, key='import_dir'),
            sg.FileBrowse(
                button_text='Import',
                key='import_btn',
                file_types=(
                    ("Proj Req", "*.projreq"),
                    ('Microsoft Excel', excel_formats),
                ),
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
        [sg.B('Save', key='save_btn', disabled=True, size=(12, 1))],
        [sg.HorizontalSeparator()],
        [
            sg.Combo(test_modules_list, key='add_type_value', size=(15, 1)),
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
            sg.Combo(params_list, key='add_param_value', size=(15, 1)),
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

        # This does not work, when file is passed, it does not get seen until an event occurs -> workaround is timeout
        if not done:
            done = True
            if proj_req is not None:
                print('Proj Req: ', proj_req)
                current_file = import_templ(proj_req, tree)
            if return_val:
                window['go_templ_btn'].Update(visible=True)



        if event == sg.WIN_CLOSED or event == 'Close' or event == 'go_templ_btn':  # if user closes window or clicks cancel
            if event == 'go_templ_btn':
                go_templ_btn_clicked = True
            break

        # print('vals', values)  # Debugging
        # print('event', event)  # Debugging

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

        if current_file is not None:
            window['current_filename_label'].Update(current_file.split(os.path.sep)[-1])
            if not is_excel:
                window['save_btn'].Update(disabled=False)
            else:
                window['save_btn'].Update(disabled=True)
        else:
            window['current_filename_label'].Update('New requirements file')

        if current_file.endswith('.projreq'):
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
