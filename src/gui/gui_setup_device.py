import os
import PySimpleGUI as sg

import src.constants as constants


def place(elem):
    """
    Places element provided into a Column element so that its placement in the layout is retained.
    :param elem: the element to put into the layout
    :return: A column element containing the provided element
    """
    return sg.Column([[elem]], pad=(0, 0))


def gui_setup_device(attached_devices, device_obj):
    select_device_frame = [[
        sg.Combo(
            attached_devices, size=(20, 20),
            key='selected_device',
            default_value=attached_devices[0],
            enable_events=True
        ),
        sg.Text(text=device_obj[attached_devices[0]].friendly_name,
                key='device-friendly',
                font="Any 18",
                size=(15, 1))
    ], ]

    logs_frame = [
        [sg.Checkbox('Capture Logs', default=False, size=(10, 1), key='logs_bool', enable_events=True)],
        [sg.Text('Logs Filter:'), sg.InputText(size=(42, 1), key='logs_filter', disabled=True)],
    ]

    select_app_frame = [[
        sg.Combo(
            values=device_obj[attached_devices[0]].get_installed_packages(),
            size=(43, 1),
            key='selected_app_package',
            default_value=device_obj[attached_devices[0]].get_current_app()[0]
        ),
        sg.Button('Test!', button_color=(sg.theme_text_element_background_color(), 'silver'), size=(5, 1),
                  key='test_app_btn', disabled=False)
    ], ]

    clickable_elements = list(device_obj[attached_devices[0]].get_clickable_window_elements().keys())

    photo_sequence_frame = []

    for num in range(constants.MAX_ACTIONS_DISPLAY):
        photo_sequence_frame += [
            # add plenty of combo boxes, disabled by default and enable the next after one has been selected
            place(sg.Combo(values=clickable_elements,
                     size=(43, 1),
                     key=f'photo_selected_action.{num}',
                     disabled=False if num == 0 else True,
                     visible=True if num == 0 else False,
                     enable_events=True)),
            place(sg.Button('Test!',
                      button_color=(sg.theme_text_element_background_color(), 'silver'),
                      size=(5, 1),
                      key=f'photo_selected_action_test_btn.{num}',
                      disabled=False if num == 0 else True,
                      visible=True if num == 0 else False))
        ],

    photo_sequence_frame += [
            sg.Button('Test sequence!',
                      button_color=(sg.theme_text_element_background_color(), 'silver'),
                      size=(45, 1),
                      key=f'photo_selected_action_sequence_test_btn',
                      disabled=False)
                            ],

    layout = [
        [sg.Frame('Select device', select_device_frame, font='Any 12', title_color='white')],
        [sg.Frame('Logs', logs_frame, font='Any 12', title_color='white')],
        [sg.Frame('Select Camera App', select_app_frame, font='Any 12', title_color='white')],
        [sg.Frame('Take Photo Action Sequence', photo_sequence_frame, font='Any 12', title_color='white')],
        [sg.Button('Save Settings', button_color=(sg.theme_text_element_background_color(), 'silver'), size=(10, 2),
                   key='save_btn', disabled=False)]
    ]

    # Create the Window
    window = sg.Window('Setup', layout,
                       icon=os.path.join(constants.ROOT_DIR, 'images', 'automated-video-testing-header-icon.ico'))

    while True:
        event, values = window.read()

        if event == sg.WIN_CLOSED or event == 'Close':  # if user closes window or clicks cancel
            break

        print('vals', values)  # Debugging
        print('event', event)  # Debugging

        if event == 'selected_device':
            window['device-friendly'].Update(device_obj[values['selected_device']].friendly_name)
            window['selected_app_package'].Update(
                values=list(device_obj[values['selected_device']].get_installed_packages()),
                value=device_obj[values['selected_device']].get_current_app()[0]
            )

            # Load device stuff
            window['photo_selected_action.0'].Update(  # TODO
                values=list(device_obj[values['selected_device']].get_clickable_window_elements().keys())
            )

        if event == "logs_bool":
            window['logs_filter'].Update(disabled=not values['logs_bool'])

        if event == 'test_app_btn':
            device_obj[values['selected_device']].open_app(values['selected_app_package'])

        if event == 'save_btn':
            # print(device_obj[attached_devices[0]].get_clickable_window_elements().keys())
            print(values)
            pass

        if event.split('.')[0] == 'photo_selected_action_test_btn':
            try:
                data = device_obj[values['selected_device']].get_clickable_window_elements()[
                    values['photo_selected_action.' + event.split('.')[1]]]
                device_obj[values['selected_device']].input_tap(data[1])
            except KeyError:
                print("Element not found! :(")

            new_ui_elements = list(device_obj[values['selected_device']].get_clickable_window_elements(force_dump=True).keys())

            for element in range(constants.MAX_ACTIONS_DISPLAY):
                if values['photo_selected_action.' + str(element)] == '':
                    window['photo_selected_action.' + str(element)].Update(values=new_ui_elements)

        if event.split('.')[0] == 'photo_selected_action':
            next_elem = int(event.split(".")[1]) + 1
            if next_elem < constants.MAX_ACTIONS_DISPLAY:
                window['photo_selected_action.' + str(next_elem)].Update(
                    disabled=False,
                    visible=True)
                window['photo_selected_action_test_btn.' + str(int(event.split(".")[1]) + 1)].Update(
                    disabled=False,
                    visible=True)

            # Update combobox elements afterwards

    window.close()
