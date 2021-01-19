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

    def add_files_in_folder(parent, dirname, level=0):
        # out_f = "files_out.txt"
        # f = open(out_f, "a")

        files = current_device.get_files_and_folders(dirname)

        logger.debug(f"Files and folders: {files}")

        for item in files:
            if item['file_type'] == 'dir':
                # if it's a folder, add folder and recurse
                fullname = os.path.join(dirname, item['name']).replace("\\", "/")  # Convert windows type slashes to unix type
                treedata.Insert(parent, fullname, item['name'], values=[],
                                icon=constants.FOLDER_ICON)

                if level != 0:
                    add_files_in_folder(fullname, fullname, level=level-1)

            elif item['file_type'] == 'file':
                fullname = os.path.join(dirname, item['name']).replace("\\", "/")  # Convert windows type slashes to unix type
                treedata.Insert(parent, fullname, item['name'], values=[f"{item['date']} {item['time']}", pretty_size(item['file_size'])],
                                icon=constants.FILE_ICON)

    # Initial data
    add_files_in_folder('', "/", 1)

    layout = [[sg.Text('Select file/s to pull:' if pull_button else
                       'Select a single element:' if single_select
                       else 'Select files/folders')],
              [sg.Tree(data=treedata, key='_TREE_', auto_size_columns=False, show_expanded=False,
                       headings=['date', 'size'], justification='center',
                       col0_width=30, col_widths=[12, 5], num_rows=20,
                       select_mode=sg.SELECT_MODE_BROWSE if single_select else sg.SELECT_MODE_EXTENDED,
                       enable_events=True, ), ],
              [sg.Input(readonly=True, key='save_dir', size=(52, 1)), sg.FolderBrowse(size=(10, 1))],
              [sg.Button('Pull', size=(57, 1)) if pull_button else sg.Button('Done', size=(57, 1))]]
    # Create the Window
    window = sg.Window('File and folder browser', layout,
                       icon=os.path.join(constants.ROOT_DIR, 'images', 'automated-video-testing-header-icon.ico'))

    while True:
        event, values = window.read()

        # window['_TREE_'].bind('<Double-Button-1>', '_double_clicked')
        # window['_TREE_'].bind('<ButtonRelease-1>', '_released')
        # window['_TREE_'].bind('<ButtonPress-1>', '_pressed')

        if event == sg.WIN_CLOSED or event == 'Close':  # if user closes window or clicks cancel
            break

        logger.debug(f'vals: {values}')  # Debugging
        logger.debug(f'event: {event}')  # Debugging
        # print(window['_TREE_'].TreeData)



    window.close()
