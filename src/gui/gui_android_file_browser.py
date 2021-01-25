import os
import PySimpleGUI as sg

from src import constants
from src.logs import logger
from src.base.utils.utils import pretty_size
from src.gui.utils_gui import collapse

DEPTH_LEVEL = 1


def gui_android_file_browser(device_obj,
                             attached_devices=None, pull_button=False, specific_device=None,
                             single_select=False, select_folder=False, read_only=False):
    # STARTING_PATH = sg.PopupGetFolder('Folder to display')
    if specific_device:
        current_device = device_obj[specific_device]
    else:
        current_device = device_obj[attached_devices[0]]

    right_click_menu = ['&File Actions', ['Info', 'Delete']]
    if read_only:
        right_click_menu = []

    treedata = sg.TreeData()
    listed_dirs = list()

    def add_files_in_folder(parent, dirname, level=0):
        # out_f = "files_out.txt"
        # f = open(out_f, "a")

        files = current_device.get_files_and_folders(dirname)

        logger.debug(f"Files and folders: {files}")

        if files is None:
            return

        for item in files:
            if item['file_type'] == 'link':
                fullname = item['link_endpoint']
            else:
                fullname = os.path.join(
                    dirname, item['name']
                ).replace("\\", "/")  # Convert windows type slashes to unix type

            if item['file_type'] == 'dir' or item['file_type'] == 'link':
                # if it's a folder, add folder and recurse
                if fullname not in listed_dirs:
                    treedata.Insert(parent, fullname, item['name'], values=[],
                                    icon=constants.FOLDER_ICON)
                    listed_dirs.append(fullname)
                if level != 0:
                    add_files_in_folder(fullname, fullname, level=level - 1)

            elif item['file_type'] == 'file' and fullname not in listed_dirs:
                treedata.Insert(parent, fullname, item['name'],
                                values=[f"{item['date']} {item['time']}", pretty_size(item['file_size'])],
                                icon=constants.FILE_ICON)
                listed_dirs.append(fullname)

    # Initial data
    add_files_in_folder('', "/", DEPTH_LEVEL)

    device_select_layout = [[
        sg.Combo(attached_devices if attached_devices else [], size=(20, 20),
                 key='selected_device',
                 default_value=attached_devices[0] if attached_devices else '',
                 enable_events=True),
        sg.Text(text=device_obj[attached_devices[0]].friendly_name if attached_devices else '',
                key='device-friendly',
                font="Any 18",
                size=(13, 1))
    ]]

    files_tree = sg.Tree(data=treedata, key='_TREE_', auto_size_columns=False, show_expanded=False,
                         headings=['date', 'size'], justification='center',
                         col0_width=30, col_widths=[12, 5], num_rows=20,
                         select_mode=sg.SELECT_MODE_BROWSE if single_select else sg.SELECT_MODE_EXTENDED,
                         enable_events=True, right_click_menu=right_click_menu, )

    pull_dest_layout = [
        [
            sg.Input(readonly=True, key='save_dir', size=(52, 1)),
            sg.FolderBrowse(size=(10, 1))
        ]
    ]

    layout = [
        [
            collapse(device_select_layout,
                     '-SEC_DEVICE_SELECT-',
                     visible=not bool(specific_device))
        ],
        [sg.Text('Select file/s to pull:' if pull_button else
                 'Select a single element:' if single_select
                 else 'Select files/folders')],
        [files_tree],
        [
            collapse(pull_dest_layout,
                     '-SEC_PULL_DEST-',
                     visible=pull_button)
        ],
        [
            sg.Button('Pull', size=(57, 1), key='pull_btn') if pull_button
            else sg.Button('Done', size=(57, 1), key='done_btn')
        ]
    ]
    # Create the Window
    window = sg.Window('File and folder browser', layout, finalize=True,
                       icon=os.path.join(constants.ROOT_DIR, 'images', 'automated-video-testing-header-icon.ico'))
    return_val = None
    while True:
        event, values = window.read()

        if event == sg.WIN_CLOSED:  # if user closes window or clicks cancel
            break

        # window['_TREE_'].bind('<Double-Button-1>', '_double_clicked')
        # window['_TREE_'].bind('<ButtonRelease-1>', '_released')
        # window['_TREE_'].bind('<ButtonPress-1>', '_pressed')
        try:
            files_tree.bind("<<TreeviewOpen>>", "EXPAND_")
            files_tree.bind("<<TreeviewClose>>", "COLLAPSE_")
        except Exception as e:
            logger.warn(e)

        if event == 'selected_device':
            window['device-friendly'].Update(device_obj[values['selected_device']].friendly_name)
            treedata = sg.TreeData()

            files_tree.update(values=treedata)
            #
            # add_files_in_folder('', "/", DEPTH_LEVEL)

            files_tree.update(values=treedata)

        # if event == '_TREE_EXPAND_':
        #     try:
        #         add_files_in_folder(values['_TREE_'][0], values['_TREE_'][0], 1)
        #         files_tree.update(values=treedata)
        #
        #         iid = None
        #         for k, v in files_tree.IdToKey.items():
        #             if v == 'Blah':
        #                 iid = k
        #                 break
        #         if iid:
        #             files_tree.Widget.see(iid)
        #             files_tree.Widget.selection_set(iid)
        #
        #     except IndexError as e:
        #         pass
        if event == 'pull_btn':
            if values['_TREE_'][0] != '':
                if values['save_dir'] == '':
                    sg.popup_auto_close("No save destination entered!")
                else:
                    current_device.pull_files_recurse(values['_TREE_'], values['save_dir'])

        if event == 'done_btn':
            if single_select and select_folder:
                filetype = current_device.get_file_type(values['_TREE_'][0])
                if filetype and filetype == 'dir':
                    return_val = values['_TREE_'][0]
                    break
                else:
                    logger.error(f'User selected a non dir, we have select_folder True')
                    sg.popup_auto_close("Make sure you are selecting a directory!")
            elif single_select:
                return_val = values['_TREE_'][0]
                break
            else:
                return_val = values['_TREE_']
                break

        logger.debug(f'vals: {values}')  # Debugging
        logger.debug(f'event: {event}')  # Debugging
        # print(window['_TREE_'].TreeData)

    window.close()
    if return_val:
        return return_val
