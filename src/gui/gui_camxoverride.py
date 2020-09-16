import os
import PySimpleGUI as sg

ROOT_DIR = os.path.abspath(os.curdir + "/../")  # This is Project Root


def gui_camxoverride(attached_devices, device_obj):
    file = os.path.join(ROOT_DIR, 'tmp', 'camxoverridesettings.txt')
    file_new = os.path.join(ROOT_DIR, 'tmp', 'camxoverridesettings_new.txt')
    print(file)
    print("Pulling camxoverridesettings.txt from device...")
    device_obj[attached_devices[0]].pull_file('/vendor/etc/camera/camxoverridesettings.txt',
                                              file)

    file_content = open(file, 'r').read().rstrip()

    # All the stuff inside your window.
    layout = [
        [sg.Combo(attached_devices, size=(20, 20), key='selected_device', default_value=attached_devices[0],
                  enable_events=True),
         sg.Text(text=device_obj[attached_devices[0]].friendly_name,
                 key='device-friendly',
                 font="Any 18")],
        [sg.Text('camxoverridesettings.txt:')],
        [sg.Multiline(file_content, size=(70, 30), key='file_input')],
        [sg.CloseButton('Close'),
         sg.Button('Save')
         ]
    ]

    # Create the Window
    window = sg.Window('Edit camxoverridesettings', layout,
                       icon=os.path.join(ROOT_DIR, 'images', 'automated-video-testing-header-icon.ico'))

    while True:
        event, values = window.read()

        if event == sg.WIN_CLOSED or event == 'Close':  # if user closes window or clicks cancel
            try:
                os.remove(file)
                os.remove(file_new)
            except FileNotFoundError:
                pass
            break

        if event == 'selected_device':
            try:
                os.remove(file)
                os.remove(file_new)
            except FileNotFoundError:
                pass

            window['device-friendly'].Update(device_obj[values['selected_device']].friendly_name)
            print("Pulling camxoverridesettings.txt from device...")
            device_obj[values['selected_device']].pull_file('/vendor/etc/camera/camxoverridesettings.txt',
                                                            file)
            file_content = open(file, 'r').read()
            window['file_input'].Update(file_content)

        if event == 'Save':
            print(values)

            print("Saving camxoverridesettings...")

            print("Generating new camxoverridesettings.txt...")
            file_new_content = open(file_new, "w")
            file_new_content.write(values['camxoverride_input'])
            file_new_content.close()

            device_obj[values['selected_device']].remount()

            print("Pushing new camxoverridesettings.txt file to device...")
            device_obj[values['selected_device']].push_file(file_new,
                                                            "/vendor/etc/camera/camxoverridesettings.txt")

    window.close()
