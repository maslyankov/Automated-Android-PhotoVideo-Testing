import os
import PySimpleGUI as sg


def gui_camxoverride(attached_devices, device_obj):
    print("Pulling camxoverridesettings.txt from device...")
    device_obj[attached_devices[0]].pull_file('/vendor/etc/camera/camxoverridesettings.txt',
                                              r'.\tmp\camxoverridesettings.txt')

    camxoverride_content = open(r'.\tmp\camxoverridesettings.txt', 'r').read().rstrip()

    # All the stuff inside your window.
    layout = [
        [sg.Combo(attached_devices, size=(20, 20), key='selected_device', default_value=attached_devices[0],
                  enable_events=True),
         sg.Text(text=device_obj[attached_devices[0]].friendly_name, key='device-friendly')],
        [sg.Text('camxoverridesettings.txt:')],
        [sg.Multiline(camxoverride_content, size=(70, 30), key='camxoverride_input')],
        [sg.CloseButton('Close'),
         sg.Button('Save')
         ]
    ]

    # Create the Window
    window = sg.Window('Edit camxoverridesettings', layout,
                       icon=r'.\images\automated-video-testing-header-icon.ico')

    while True:
        event, values = window.read()

        if event == sg.WIN_CLOSED or event == 'Close':  # if user closes window or clicks cancel
            try:
                os.remove(r'.\tmp\camxoverridesettings.txt')
                os.remove(r'.\tmp\camxoverridesettings_new.txt')
            except FileNotFoundError:
                pass
            break

        if event == 'selected_device':
            try:
                os.remove(r'.\tmp\camxoverridesettings.txt')
                os.remove(r'.\tmp\camxoverridesettings_new.txt')
            except FileNotFoundError:
                pass

            window['device-friendly'].Update(device_obj[values['selected_device']].friendly_name)
            print("Pulling camxoverridesettings.txt from device...")
            device_obj[values['selected_device']].pull_file('/vendor/etc/camera/camxoverridesettings.txt',
                                                            r'.\tmp\camxoverridesettings.txt')
            camxoverride_content = open(r'.\tmp\camxoverridesettings.txt', 'r').read()
            window['camxoverride_input'].Update(camxoverride_content)

        if event == 'Save':
            print(values)

            print("Saving camxoverridesettings...")

            print("Generating new camxoverridesettings.txt...")
            camxoverride_new = open(r'.\tmp\camxoverridesettings_new.txt', "w")
            camxoverride_new.write(values['camxoverride_input'])
            camxoverride_new.close()

            device_obj[values['selected_device']].remount()

            print("Pushing new camxoverridesettings.txt file to device...")
            device_obj[values['selected_device']].push_file(r'.\tmp\camxoverridesettings_new.txt',
                                                            "/vendor/etc/camera/camxoverridesettings.txt")

    window.close()
