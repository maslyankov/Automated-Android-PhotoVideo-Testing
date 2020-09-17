import os
import PySimpleGUI as sg
from pathlib import Path

import src.constants as constants


def gui_push_file(attached_devices, device_obj):
    file_destinations = [
        'sdcard/DCIM/',
        'vendor/lib/camera/'
    ]

    layout = [
        [
            sg.Text('Device: ', size=(9, 1)),
            sg.Combo(attached_devices, size=(20, 20),
                     enable_events=True, key='selected_device',
                     default_value=attached_devices[0]),
            sg.Text(text=device_obj[attached_devices[0]].friendly_name,
                    key='device-friendly',
                    font="Any 18")
        ],
        [
            sg.Text('Destination: ', size=(9, 1)),
            sg.Combo(file_destinations, size=(20, 20), key='dest_folder', default_value=file_destinations[0])
        ],
        [
            sg.Text('File:', size=(9, 1)),
            sg.InputText(size=(35, 1), key='source_file', enable_events=True),
            sg.FileBrowse()
        ],
        [sg.Button('Push File', button_color=(sg.theme_text_element_background_color(), 'silver'), size=(10, 2),
                   key='push_file_btn', disabled=True)]
    ]

    # Create the Window
    window = sg.Window('Push file file', layout,
                       icon=os.path.join(constants.ROOT_DIR, 'images', 'automated-video-testing-header-icon.ico'))

    while True:
        event, values = window.read()

        if event == sg.WIN_CLOSED or event == 'Close':  # if user closes window or clicks cancel
            break

        print('vals', values)  # Debugging
        print('event', event)  # Debugging

        if event == 'selected_device':
            window['device-friendly'].Update(device_obj[values['selected_device']].friendly_name)

        if event == 'source_file':
            window['push_file_btn'].Update(disabled=False)

        if event == 'push_file_btn':
            curr_device = device_obj[values['selected_device']]
            file_dest = values['dest_folder']
            filename = Path(values['source_file']).name

            print("Remounting Device...")
            curr_device.remount()

            print("Pushing new file to device...")

            curr_device.push_file(values['source_file'], file_dest + filename)

    window.close()
