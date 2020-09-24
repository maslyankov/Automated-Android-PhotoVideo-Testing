import os
import PySimpleGUI as sg

import src.constants as constants


def gui_help():
    general_info = [
        [sg.Text("First tick checkbox next to the device you want to connect to \n" +
                 "in order to access other functions of this app:")],
        [sg.Text("- File editing \n" +
                 "- File transfer \n" +
                 "- Device Control \n" +
                 "- Device Setup")]
    ]

    lights_info = [
        [sg.Text(
            "First select the lights you want to connect to, then if you want, \n" +
            "select what luxmeter is connected and then you can open \n" +
            "the Lights Test GUI by clicking the 'Test Lights' button.")],
        [sg.Text('Lights Control gives you the ability to:')],
        [sg.Text("- Change Color Temperature\n" +
                 "- Control light bulbs individually or all at once\n" +
                 "- Set light brightness\n" +
                 "- Get light measurements using a connected Luxmeter")]
    ]

    device_screen_ctrl = [
        [sg.Text("Switch to fullscreen mode", size=(35, 1)), sg.Text('Alt (left) + F', text_color='orange')],
        [sg.Text("Resize window to remove black borders", size=(35, 1)), sg.Text('Alt (left) + W', text_color='orange')],

        [sg.Text("Home", size=(35, 1)), sg.Text('Alt (left) + H', text_color='orange')],
        [sg.Text("Back", size=(35, 1)), sg.Text('Alt (left) + B', text_color='orange')],
        [sg.Text("App Switcher", size=(35, 1)), sg.Text('Alt (left) + S', text_color='orange')],
        [sg.Text("Menu (Unlock Screen)", size=(35, 1)), sg.Text('Alt (left) + M', text_color='orange')],
        [sg.Text("Rotate Device Screen", size=(35, 1)), sg.Text('Alt (left) + R', text_color='orange')],
    ]

    layout = [
        [
            sg.Text('How to', font='Any 24'),
        ],
        [sg.Frame("General", general_info, font='Any 12', title_color='white')],
        [sg.Frame("Lights", lights_info, font='Any 12', title_color='white')],
        [sg.Frame("Device Screen Control", device_screen_ctrl, font='Any 12', title_color='white')]
    ]

    # Create the Window
    window = sg.Window('App Help', layout,
                       icon=os.path.join(constants.ROOT_DIR, 'images', 'automated-video-testing-header-icon.ico'))

    while True:
        event, values = window.read()

        if event == sg.WIN_CLOSED or event == 'Close':  # if user closes window or clicks cancel
            break

    window.close()
