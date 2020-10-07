import os
import PySimpleGUI as sg

import src.constants as constants


def list_from_data(values, fltr):
    seq = []
    print('List from data got: ', values)
    for item in values.keys():
        if values[item] == 'Empty':
            continue  # Skip empty items

        if item.split('.')[0] == fltr and values[item] != '':
            if values[item.replace("action", "action_type")] == 'tap':
                value = [
                    values[item.replace("action", "action_x")],
                    values[item.replace("action", "action_y")]
                ]
            else:
                value = values[item.replace("action", "action_value")]
            seq.append([
                values[item], [
                    values[item.replace("action", "action_desc")],
                    value,
                    values[item.replace("action", "action_type")]
                ]
            ])
    print('Created seq: ', seq)
    return seq


def device_data_to_gui(device, window):
    print("Parsing device object data and updating GUI accordingly...\n")

    device.print_attributes()

    clickable_elements = constants.CUSTOM_ACTIONS + list(device.get_clickable_window_elements().keys())

    # Update window elements
    window['device-friendly'].Update(device.friendly_name)

    window['logs_bool'].Update(value=True if device.logs_enabled else False)

    print(device.logs_filter)
    window['logs_filter'].Update(device.logs_filter)

    window['selected_app_package'].Update(
        values=list(device.get_installed_packages()),
        value=device.get_current_app()[0] if device.camera_app is None else device.camera_app
    )

    # List
    for seq_type in list(constants.ACT_SEQUENCES.keys()):
        # Cleanup before populating
        for row in range(constants.MAX_ACTIONS_DISPLAY):
            print('Clearing row ', row)  # Debugging

            window[f'{seq_type}_selected_action.' + str(row)].Update('Empty', values='', disabled=True, visible=False)
            window[f'{seq_type}_selected_action_test_btn.' + str(row)].Update(disabled=True, visible=False)

            window[f'{seq_type}_selected_action_desc.' + str(row)].Update('Empty')
            window[f'{seq_type}_selected_action_value.' + str(row)].Update(0)
            window[f'{seq_type}_selected_action_x.' + str(row)].Update('Empty')
            window[f'{seq_type}_selected_action_y.' + str(row)].Update('Empty')
            window[f'{seq_type}_selected_action_type.' + str(row)].Update('Empty')

        for act_num, action in enumerate(getattr(device, constants.ACT_SEQUENCES[seq_type])):
            print('Populating row ', act_num)
            if act_num > constants.MAX_ACTIONS_DISPLAY:
                print("Max displayable actions reached!")
                break

            window[f'{seq_type}_selected_action.' + str(act_num)].Update(
                value=action[0],
                values=clickable_elements,
                visible=True,
                disabled=False
            )
            window[f'{seq_type}_selected_action_test_btn.' + str(act_num)].Update(
                disabled=False,
                visible=True)

            window[f'{seq_type}_selected_action_type.' + str(act_num)].Update(
                value=action[1][2]
            )
            window[f'{seq_type}_selected_action_desc.' + str(act_num)].Update(value=action[1][0])

            if action[1][2] == 'tap':
                window[f'{seq_type}_selected_action_x.' + str(act_num)].Update(value=action[1][1][0])
                window[f'{seq_type}_selected_action_y.' + str(act_num)].Update(value=action[1][1][1])
                window[f'{seq_type}_selected_action_value.' + str(act_num)].Update(value=0, visible=False,
                                                                                   disabled=True)
            else:
                window[f'{seq_type}_selected_action_value.' + str(act_num)].Update(value=action[1][1], visible=True,
                                                                                   disabled=False)
                window[f'{seq_type}_selected_action_test_btn.' + str(act_num)].Update(visible=False, disabled=True)

            next_elem = act_num + 1
            clickable_elements = constants.CUSTOM_ACTIONS + list(
                device.get_clickable_window_elements().keys())
            if next_elem < constants.MAX_ACTIONS_DISPLAY:
                window[f'{seq_type}_selected_action.' + str(next_elem)].Update(
                    values=clickable_elements,
                    disabled=False,
                    visible=True)
                window[f'{seq_type}_selected_action_test_btn.' + str(next_elem)].Update(
                    disabled=False,
                    visible=True)

    # Actions Gap
    window['actions_gap_spinner'].Update(
        value=getattr(device, 'actions_time_gap')
    )


def build_seq_gui(obj, prop_key, clickable_elements):  # TODO - Fix list of actions to choose from
    gui_seq = []
    print("GUI Builder got: ", obj, prop_key, clickable_elements)

    for num in range(constants.MAX_ACTIONS_DISPLAY):
        if getattr(obj, constants.ACT_SEQUENCES[prop_key]) != [] and len(
                getattr(obj, constants.ACT_SEQUENCES[prop_key])) > num:
            current_obj_elem = getattr(obj, constants.ACT_SEQUENCES[prop_key])[num]
        else:
            current_obj_elem = None

        gui_seq += [
                       # add plenty of combo boxes, disabled by default and
                       # enable the next after one has been selected
                       place(sg.Combo(
                           default_value=
                           'Empty' if current_obj_elem is None
                           else current_obj_elem[0],
                           values=clickable_elements,
                           size=(37, 1),
                           key=f'{prop_key}_selected_action.{num}',
                           disabled=False if num == 0 or num == len(getattr(obj, constants.ACT_SEQUENCES[
                               prop_key])) or current_obj_elem is not None else True,
                           visible=True if num == 0 or num == len(getattr(obj, constants.ACT_SEQUENCES[
                               prop_key])) or current_obj_elem is not None else False,
                           enable_events=True
                       )),
                       sg.Spin(
                           [i for i in range(1, 10)],
                           initial_value=
                           1 if current_obj_elem is None
                           else
                           current_obj_elem[1][1] if current_obj_elem[1][2] != 'tap' else 1,
                           key=f'{prop_key}_selected_action_value.{num}',
                           disabled=True,
                           visible=False
                       ),
                       place(sg.Button(
                           'Test!',
                           button_color=(sg.theme_text_element_background_color(), 'silver'),
                           size=(4, 1),
                           key=f'{prop_key}_selected_action_test_btn.{num}',
                           disabled=False if num == 0 or num == len(getattr(obj, constants.ACT_SEQUENCES[
                               prop_key])) or current_obj_elem is not None else True,
                           visible=True if num == 0 or num == len(getattr(obj, constants.ACT_SEQUENCES[
                               prop_key])) or current_obj_elem is not None else False
                       )),

                       # to keep data
                       sg.InputText(
                           'Empty' if current_obj_elem is None
                           else current_obj_elem[1][0],
                           key=f'{prop_key}_selected_action_desc.{num}',
                           readonly=True,
                           visible=False
                       ),
                       sg.InputText(
                           'Empty' if current_obj_elem is None
                           else current_obj_elem[1][1][0] if current_obj_elem[1][2] == 'tap'
                           else current_obj_elem[1][1],
                           key=f'{prop_key}_selected_action_x.{num}',
                           readonly=True,
                           visible=False
                       ),
                       sg.InputText(
                           'Empty' if current_obj_elem is None or current_obj_elem[1][2] != 'tap'
                           else current_obj_elem[1][1][1],
                           key=f'{prop_key}_selected_action_y.{num}',
                           readonly=True,
                           visible=False
                       ),
                       sg.InputText(
                           'Empty' if current_obj_elem is None
                           else current_obj_elem[1][2],
                           key=f'{prop_key}_selected_action_type.{num}',
                           readonly=True,
                           visible=False
                       ),
                   ],
    gui_seq += [
                   sg.Button('Test sequence!',
                             button_color=(sg.theme_text_element_background_color(), 'silver'),
                             size=(42, 1),
                             key=f'{prop_key}_selected_action_sequence_test_btn',
                             disabled=False)
               ],
    return gui_seq


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

    print('Device Logs filter:', device_obj[attached_devices[0]].logs_filter)

    logs_frame = [  # TODO Update with element info if available
        [sg.Checkbox('Capture Logs',
                     default=True if device_obj[attached_devices[0]].logs_enabled else False,
                     size=(10, 1),
                     key='logs_bool',
                     enable_events=True)],
        [sg.Text('Logs Filter:'),
         sg.InputText(size=(42, 1),
                      key='logs_filter',
                      default_text=device_obj[attached_devices[0]].logs_filter,
                      disabled=False if device_obj[attached_devices[0]].logs_enabled else True)],
    ]

    current_app = device_obj[attached_devices[0]].get_current_app()
    if current_app is None:
        current_app = ['...', '...']

    select_app_frame = [
        [sg.Text('Currently:')],
        [sg.Text(current_app[0],
                 key='currently_opened_app',
                 font='Any 13')],
        [sg.Text(current_app[1],
                 key='current_app_activity',
                 font='Any 13')],
        [
            sg.Combo(
                values=device_obj[attached_devices[0]].get_installed_packages(),
                size=(43, 1),
                key='selected_app_package',
                default_value=device_obj[attached_devices[0]].get_camera_app_pkg() if device_obj[attached_devices[
                    0]].get_camera_app_pkg() is not None else ''
            ),
            sg.Button('Test!',
                      button_color=(sg.theme_text_element_background_color(), 'silver'),
                      size=(5, 1),
                      key='test_app_btn', disabled=False)
        ], ]

    actions_seq_settings_frame = [
        [
            sg.Text('Actions Gap Time:'),
            sg.Spin([i for i in range(0, 30)],
                    initial_value=getattr(device_obj[attached_devices[0]], 'actions_time_gap'),
                    key='actions_gap_spinner',
                    disabled=False,
                    enable_events=True)
        ],
    ]

    # - Sequences -
    clickable_elements = constants.CUSTOM_ACTIONS + list(
        device_obj[attached_devices[0]].get_clickable_window_elements().keys())

    seq_column = []

    for elem in list(constants.ACT_SEQUENCES.keys()):
        frame = [sg.Frame(f'{constants.ACT_SEQUENCES_DESC[elem]} Action Sequence',
                          build_seq_gui(device_obj[attached_devices[0]], elem, clickable_elements), font='Any 12',
                          title_color='white')]
        seq_column.append(frame)

    layout = [
        [sg.Frame('Select device', select_device_frame, font='Any 12', title_color='white')],
        [sg.Frame('Logs', logs_frame, font='Any 12', title_color='white')],
        [sg.Frame('Select Camera App', select_app_frame, font='Any 12', title_color='white')],
        [sg.Frame('Actions Sequences Settings', actions_seq_settings_frame, font='Any 12', title_color='white')],
        [sg.Column(seq_column, size=(370, 230), scrollable=True, vertical_scroll_only=True)],
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

        current_app = device_obj[attached_devices[0]].get_current_app()
        if current_app is None:
            current_app = ['...', '...']

        window['currently_opened_app'].Update(current_app[0])
        window['current_app_activity'].Update(current_app[1])

        if event == 'selected_device':
            device_data_to_gui(device_obj[values['selected_device']], window)

        if event == "logs_bool":
            window['logs_filter'].Update(disabled=not values['logs_bool'])

        if event == 'test_app_btn':
            device_obj[values['selected_device']].open_app(values['selected_app_package'])

            new_ui_elements = constants.CUSTOM_ACTIONS + list(
                device_obj[values['selected_device']].get_clickable_window_elements().keys())

            for seq_type in list(constants.ACT_SEQUENCES.keys()):
                for element in range(constants.MAX_ACTIONS_DISPLAY):
                    # if values[f'{seq_type}_selected_action.{str(element)}'] == 'Empty':
                    window[f'{seq_type}_selected_action.{str(element)}'].Update(values=new_ui_elements)

        if event == 'actions_gap_spinner':
            setattr(device_obj[values['selected_device']], 'actions_time_gap', values['actions_gap_spinner'])

        for seq_type in list(constants.ACT_SEQUENCES.keys()):
            if event.split('.')[0] == f'{seq_type}_selected_action':
                if values[f"{seq_type}_selected_action.{event.split('.')[1]}"] == 'delay':
                    window[f"{seq_type}_selected_action_type.{event.split('.')[1]}"].Update('delay')
                    window[f"{seq_type}_selected_action_value.{event.split('.')[1]}"].Update(visible=True,
                                                                                             disabled=False)
                    window[f"{seq_type}_selected_action_test_btn.{event.split('.')[1]}"].Update(visible=False,
                                                                                                disabled=True)
                elif values[f"{seq_type}_selected_action.{event.split('.')[1]}"] == 'Empty':
                    pass
                else:
                    data = device_obj[values['selected_device']].get_clickable_window_elements()[
                        values[f'{seq_type}_selected_action.' + event.split('.')[1]]
                    ]
                    window[f"{seq_type}_selected_action_type.{event.split('.')[1]}"].Update('tap')
                    window[f"{seq_type}_selected_action_desc.{event.split('.')[1]}"].Update(data[0])  # save for later
                    window[f"{seq_type}_selected_action_x.{event.split('.')[1]}"].Update(data[1][0])  # save for later
                    window[f"{seq_type}_selected_action_y.{event.split('.')[1]}"].Update(data[1][1])  # save for later
                next_elem = int(event.split(".")[1]) + 1
                if next_elem < constants.MAX_ACTIONS_DISPLAY:
                    window[f"{seq_type}_selected_action.{str(next_elem)}"].Update(
                        disabled=False,
                        visible=True)
                    window[f"{seq_type}_selected_action_test_btn.{str(next_elem)}"].Update(
                        disabled=False,
                        visible=True)

            if event.split('.')[
                0] == f"{seq_type}_selected_action_test_btn":  # TODO - Make this use the GUI values not obj values
                try:
                    data = device_obj[values['selected_device']].get_clickable_window_elements()[
                        values[f"{seq_type}_selected_action.{event.split('.')[1]}"]
                    ]
                    device_obj[values['selected_device']].input_tap(data[1])
                except KeyError:
                    print("Element not found! :(")

                new_ui_elements = constants.CUSTOM_ACTIONS + list(
                    device_obj[values['selected_device']].get_clickable_window_elements(force_dump=True).keys())

                for element in range(constants.MAX_ACTIONS_DISPLAY):
                    if values[f"{seq_type}_selected_action.{str(element)}"] == 'Empty':
                        window[f"{seq_type}_selected_action.{str(element)}"].Update(values=new_ui_elements)

            if event == f"{seq_type}_selected_action_sequence_test_btn":
                device_obj[values['selected_device']].do(getattr(device_obj[values['selected_device']], constants.ACT_SEQUENCES[seq_type]))

        if event == 'save_btn':
            device = device_obj[values['selected_device']]
            # Save to object
            device.set_logs(values['logs_bool'], values['logs_filter'])
            device.set_camera_app_pkg(values['selected_app_package'])
            for seq_type in list(constants.ACT_SEQUENCES.keys()):
                val = list_from_data(values, f'{seq_type}_selected_action')
                setattr(device, constants.ACT_SEQUENCES[seq_type], val)

            # Save to file
            device.save_settings()
            print("Device logs settings: ", device_obj[values['selected_device']].logs_enabled,
                  device_obj[values['selected_device']].logs_filter)
            print('Device photo seq: ', device_obj[values['selected_device']].shoot_photo_seq)

    window.close()
