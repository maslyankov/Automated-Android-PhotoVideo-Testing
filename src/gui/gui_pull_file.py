import os
import PySimpleGUI as sg

import src.constants as constants


def gui_pull_file(attached_devices, device_obj):
    #STARTING_PATH = sg.PopupGetFolder('Folder to display')

    current_device = device_obj[attached_devices[0]]

    folder_icon = constants.FOLDER_ICON
    file_icon = constants.FILE_ICON

    treedata = sg.TreeData()

    def add_files_in_folder(parent, dirname):
        folders = current_device.get_dirs_list(dirname)
        files = current_device.get_only_files_list(dirname)
        print(f"folders:'{files}'\n")
        print(f"files:'{files}'\n\n\n")

        for f in folders:
            fullname = os.path.join(dirname, f)
            # if os.path.isdir(fullname):  # if it's a folder, add folder and recurse
            treedata.Insert(parent, fullname, f, values=[],
                            icon=folder_icon)
            add_files_in_folder(fullname, fullname)

        for f in files:
            fullname = os.path.join(dirname, f)
            treedata.Insert(parent, fullname, f, values=["14/12/2020 01:22", "22.5 MB"],
                            icon=file_icon)


    add_files_in_folder('', "/")

    layout = [[sg.Text('File and folder browser Test')],
              [sg.Tree(data=treedata, headings=['date', 'size'], auto_size_columns=True, num_rows=20,
                       col0_width=30, key='_TREE_', show_expanded=False, enable_events=True, ),],
              [sg.Button('Ok'), sg.Button('Cancel')]]
    # Create the Window
    window = sg.Window('Pull file/s', layout,
                       icon=os.path.join(constants.ROOT_DIR, 'images', 'automated-video-testing-header-icon.ico'))

    while True:
        event, values = window.read()

        if event == sg.WIN_CLOSED or event == 'Close':  # if user closes window or clicks cancel
            break

        print('vals', values)  # Debugging
        print('event', event)  # Debugging

    window.close()
