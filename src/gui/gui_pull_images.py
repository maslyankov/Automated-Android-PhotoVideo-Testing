import os
import PySimpleGUI as sg

from src import constants
from src.logs import logger
from src.gui.utils_gui import collapse


def gui_pull_images(device_obj, attached_devices=None, specific_device=None):
    if specific_device:
        device_obj[specific_device].load_settings_file()
        persist_setting = device_obj[specific_device].get_persist_setting('last_pull_images_save_dest')
    else:
        device_obj[specific_device].load_settings_file()
        persist_setting = device_obj[attached_devices[0]].get_persist_setting('last_pull_images_save_dest')

    select_device_layout = [
        [
            sg.Text('Device: ', size=(9, 1)),
            sg.Combo(attached_devices if attached_devices else [], size=(20, 20),
                     enable_events=True, key='selected_device',
                     default_value=attached_devices[0] if attached_devices else ""),
            sg.Text(text=device_obj[attached_devices[0]].friendly_name if attached_devices else "",
                    key='device-friendly',
                    size=(13, 1),
                    font="Any 18")
        ]
    ]

    layout = [
        [collapse(select_device_layout, 'select_device_layout', not bool(specific_device))],
        [
            sg.T("Save destination:"),
            sg.I(key='save_dest',
                 default_text=persist_setting if persist_setting else ""),
            sg.FolderBrowse()
        ],
        [sg.Button('Pull', size=(10, 2),
                   key='pull_btn', disabled=False)]
    ]

    # Create the Window
    window = sg.Window('Reboot Device', layout,
                       icon=os.path.join(constants.ROOT_DIR, 'images', 'automated-video-testing-header-icon.ico'))

    while True:
        event, values = window.read()

        if event == sg.WIN_CLOSED or event == 'Close':  # if user closes window or clicks cancel
            break

        logger.debug(f"Event: {event}")  # Debugging
        logger.debug(f"Values: {values}")  # Debugging

        curr_device = device_obj[values['selected_device']] if not specific_device else device_obj[specific_device]

        if attached_devices and event == 'selected_device':
            window['device-friendly'].Update(curr_device.friendly_name)

            persist_setting = curr_device.get_persist_setting('last_pull_images_save_dest')
            window['dest_folder'].Update(persist_setting)

        if event == 'pull_btn':
            logger.info(f"Pulling from device {values['selected_device']}")

            save_dir = values['save_dest']

            if save_dir and os.path.isdir(save_dir):
                device_images_dir = curr_device.images_save_loc
                # files_to_pull = adb_devices[attached_devices_list[0]].get_recursive_files_list(device_images_dir)
                # print(files_to_pull)

                curr_device.set_persist_setting("last_pull_images_save_dest", save_dir)
                curr_device.save_settings()

                curr_device.pull_files_recurse(
                    curr_device.get_files_list(device_images_dir, get_full_path=True),
                    save_dir
                )

    window.close()
