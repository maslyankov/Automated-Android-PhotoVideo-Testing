import os
import PySimpleGUI as sg

from src import constants
from src.logs import logger


def gui_pull_file(attached_devices, device_obj):
    # STARTING_PATH = sg.PopupGetFolder('Folder to display')

    current_device = device_obj[attached_devices[0]]

    folder_icon = constants.FOLDER_ICON
    file_icon = constants.FILE_ICON

    treedata = sg.TreeData()

    def add_files_in_folder(parent, dirname):
        # out_f = "files_out.txt"
        # f = open(out_f, "a")

        files = current_device.get_files_and_folders(dirname)

        logger.debug(f"Files and folders: {files}")
        # f.write(str(files))
        # f.close()



        # logger.debug(f"files:'{files}'")

        # for f in folders:
        #     fullname = os.path.join(dirname, f)
        #     # if os.path.isdir(fullname):  # if it's a folder, add folder and recurse
        #     treedata.Insert(parent, fullname, f, values=[],
        #                     icon=folder_icon)
        #     add_files_in_folder(fullname, fullname)
        #
        # for f in files:
        #     fullname = os.path.join(dirname, f)
        #     treedata.Insert(parent, fullname, f, values=["14/12/2020 01:22", "22.5 MB"],
        #                     icon=file_icon)

    add_files_in_folder('', "/")

    layout = [[sg.Text('File and folder browser Test')],
              [sg.Tree(data=treedata, headings=['date', 'size'], auto_size_columns=True, num_rows=20,
                       col0_width=30, key='_TREE_', show_expanded=False, enable_events=True, ), ],
              [sg.Button('Ok'), sg.Button('Cancel')]]
    # Create the Window
    window = sg.Window('Pull file/s', layout,
                       icon=os.path.join(constants.ROOT_DIR, 'images', 'automated-video-testing-header-icon.ico'))

    while True:
        event, values = window.read()

        if event == sg.WIN_CLOSED or event == 'Close':  # if user closes window or clicks cancel
            break

        logger.debug(f'vals: {values}')  # Debugging
        logger.debug(f'event: {event}')  # Debugging

    window.close()
