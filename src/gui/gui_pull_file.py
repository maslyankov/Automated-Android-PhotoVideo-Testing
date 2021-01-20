import os
import PySimpleGUI as sg

from src import constants
from src.logs import logger
from src.code.utils.utils import pretty_size


def gui_android_file_browser(attached_devices, device_obj, pull_button=False, single_select=False):
    # STARTING_PATH = sg.PopupGetFolder('Folder to display')

    current_device = device_obj[attached_devices[0]]

    folder_icon = constants.FOLDER_ICON
    file_icon = constants.FILE_ICON

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
    add_files_in_folder('', "/", 1)

    files_tree = sg.Tree(data=treedata, key='_TREE_', auto_size_columns=False, show_expanded=False,
                         headings=['date', 'size'], justification='center',
                         col0_width=30, col_widths=[12, 5], num_rows=20,
                         select_mode=sg.SELECT_MODE_BROWSE if single_select else sg.SELECT_MODE_EXTENDED,
                         enable_events=True, )

    layout = [[sg.Text('Select file/s to pull:' if pull_button else
                       'Select a single element:' if single_select
                       else 'Select files/folders')],
              [files_tree],
              [sg.Input(readonly=True, key='save_dir', size=(52, 1)), sg.FolderBrowse(size=(10, 1))],
              [sg.Button('Pull', size=(57, 1)) if pull_button else sg.Button('Done', size=(57, 1))]]
    # Create the Window
    window = sg.Window('File and folder browser', layout, finalize=True,
                       icon=os.path.join(constants.ROOT_DIR, 'images', 'automated-video-testing-header-icon.ico'))

    while True:
        event, values = window.read()

        # window['_TREE_'].bind('<Double-Button-1>', '_double_clicked')
        # window['_TREE_'].bind('<ButtonRelease-1>', '_released')
        # window['_TREE_'].bind('<ButtonPress-1>', '_pressed')
        window['_TREE_'].bind("<<TreeviewOpen>>", "EXPAND_")
        window['_TREE_'].bind("<<TreeviewClose>>", "COLLAPSE_")

        if event == sg.WIN_CLOSED or event == 'Done':  # if user closes window or clicks cancel
            if event == 'Done':
                return values['_TREE_']

            break

        if event == '_TREE_EXPAND_':
            try:
                add_files_in_folder(values['_TREE_'][0], values['_TREE_'][0], 1)
                files_tree.update(values=treedata)

                iid = None
                for k, v in files_tree.IdToKey.items():
                    if v == 'Blah':
                        iid = k
                        break
                if iid:
                    files_tree.Widget.see(iid)
                    tree.Widget.selection_set(iid)

            except IndexError as e:
                pass

        logger.debug(f'vals: {values}')  # Debugging
        logger.debug(f'event: {event}')  # Debugging
        # print(window['_TREE_'].TreeData)

    window.close()
