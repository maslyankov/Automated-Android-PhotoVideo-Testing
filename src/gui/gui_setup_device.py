import os
import PySimpleGUI as sg

ROOT_DIR = os.path.abspath(os.curdir + "/../")  # This is Project Root


def gui_setup_device(attached_devices, device_obj):
    select_device_frame = [[
        sg.Combo(
            attached_devices, size=(20, 20),
            key='selected_device',
            default_value=attached_devices[0],
            enable_events=True
        ),
        sg.Text(text=device_obj[attached_devices[0]].friendly_name, key='device-friendly')
    ], ]

    select_app_frame = [[
        sg.Combo(
            values=device_obj[attached_devices[0]].get_installed_packages(),
            size=(40, 1),
            key='selected_app_package',
            default_value=device_obj[attached_devices[0]].get_current_app()[0]
        ),
        sg.Button('Test it!', button_color=(sg.theme_text_element_background_color(), 'silver'), size=(10, 1),
                  key='test_app_btn', disabled=False)
    ], ]

    photo_sequence_frame = [[  # add plenty of combo boxes, disabled by default and enable them after first is occupied
        sg.Combo(values=list(device_obj[attached_devices[0]].get_clickable_window_elements().keys()), size=(40, 1),
                 key='photo_selected_action.0'),
        sg.Button('Test it!', button_color=(sg.theme_text_element_background_color(), 'silver'), size=(10, 1),
                  key='test_btn_photo_selected_action.0', disabled=False)
    ], ]

    layout = [
        [sg.Frame('Select device', select_device_frame, font='Any 12', title_color='white')],
        [sg.Frame('Select Camera App', select_app_frame, font='Any 12', title_color='white')],
        [sg.Frame('Take Photo Action Sequence', photo_sequence_frame, font='Any 12', title_color='white')],
        [sg.Button('Save Settings', button_color=(sg.theme_text_element_background_color(), 'silver'), size=(10, 2),
                   key='save_btn', disabled=False)]
    ]

    # Create the Window
    window = sg.Window('Setup', layout,
                       icon=os.path.join(ROOT_DIR, 'images', 'automated-video-testing-header-icon.ico'))

    while True:
        event, values = window.read()

        if event == sg.WIN_CLOSED or event == 'Close':  # if user closes window or clicks cancel
            break

        print('vals', values)  # Debugging
        print('event', event)  # Debugging

        if event == 'test_app_btn':
            device_obj[values['selected_device']].open_app(values['selected_app_package'])

        if event == 'selected_device':
            window['device-friendly'].Update(device_obj[values['selected_device']].friendly_name)
            window['selected_app_package'].Update(
                values=list(device_obj[values['selected_device']].get_installed_packages()),
                value=device_obj[values['selected_device']].get_current_app()[0]
            )
            window['photo_selected_action.0'].Update(  # TODO
                values=list(device_obj[values['selected_device']].get_clickable_window_elements().keys())
            )

        if event == 'save_btn':
            # print(device_obj[attached_devices[0]].get_clickable_window_elements().keys())
            pass

        if event.split('.')[0] == 'test_btn_photo_selected_action':
            try:
                data = device_obj[values['selected_device']].get_clickable_window_elements()[
                    values['photo_selected_action.' + event.split('.')[1]]]
                device_obj[values['selected_device']].input_tap(data[1])
            except KeyError:
                print("Element not found! :(")

            # Update combobox elements afterwards

    window.close()
