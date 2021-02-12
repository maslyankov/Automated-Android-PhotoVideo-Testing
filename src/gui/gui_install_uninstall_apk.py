import os
import PySimpleGUI as sg

from src import constants
from src.logs import logger
from src.gui.utils_gui import collapse


def gui_install_uninstall_apk(device_obj, attached_devices=None, specific_device=None):
    # if specific_device:
    #     device_obj[specific_device].load_settings_file()
    #     persist_setting = device_obj[specific_device].get_persist_setting('last_pull_images_save_dest')
    # else:
    #     device_obj[specific_device].load_settings_file()
    #     persist_setting = device_obj[attached_devices[0]].get_persist_setting('last_pull_images_save_dest')

    curr_device = device_obj[attached_devices[0]] if not specific_device else device_obj[specific_device]

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

    apks_list = curr_device.get_installed_packages()

    layout = [
        [collapse(select_device_layout, 'select_device_layout', not bool(specific_device))],
        [
            sg.Listbox(values=apks_list, size=(50, 10), k='uninstall_apk_selected'),
            sg.B('Uninstall\nAPK', size=(20, 5), key='uninstall_apk_btn', disabled=False)
        ],
        [
            sg.T("Install apk:"),
            sg.I(key='install_selected_apk'),
            sg.FileBrowse(
                file_types=(
                    ("Android APK", "*.apk"),
                )),
            sg.B('Install APK', size=(10, 1), key='install_apk_btn', disabled=False)
        ],

    ]

    # Create the Window
    window = sg.Window('Install/Uninstall APK', layout,
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

        if event == 'install_apk_btn':
            if os.path.isfile(values['install_selected_apk']):
                curr_device.install_apk(values['install_selected_apk'])
                sg.popup_ok(f"{values['install_selected_apk']} installed!")

        if event == 'uninstall_apk_btn':
            if values['uninstall_apk_selected'] and \
                    sg.popup_yes_no(f"Are you sure you want to uninstall {values['uninstall_apk_selected'][0]}"):
                curr_device.uninstall_apk(values['uninstall_apk_selected'][0])
                sg.popup_ok(f"{values['uninstall_apk_selected'][0]} uninstalled!")

    window.close()
