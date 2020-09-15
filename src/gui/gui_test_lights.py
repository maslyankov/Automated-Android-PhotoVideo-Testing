import os
import PySimpleGUI as sg
from src.app.LightsCtrl import LightsCtrl

ROOT_DIR = os.path.abspath(os.curdir + "/../")  # This is Project Root


def gui_test_lights(selected_lights_model):
    if selected_lights_model == 'SpectriWave':
        status_layout = [
                sg.Text(text='Left Side:', font="Any 24", size=(10, 1)),

                sg.Text(text='Relay - '),
                sg.Text(text="Loading",
                        size=(15, 1),
                        key='is-connected-0-relay',
                        text_color="black",
                        background_color="red"),
                sg.Text(text='Dimmer - '),
                sg.Text(text="Loading",
                        size=(15, 1),
                        key='is-connected-0-dimmer',
                        text_color="black",
                        background_color="red"),

                sg.VerticalSeparator(),

                sg.Text(text='Right Side:', font="Any 24", size=(10, 1)),

                sg.Text(text='Relay - '),
                sg.Text(text="Loading",
                        size=(15, 1),
                        key='is-connected-1-relay',
                        text_color="black",
                        background_color="red"),
                sg.Text(text='Dimmer - '),
                sg.Text(text="Loading",
                        size=(15, 1),
                        key='is-connected-1-dimmer',
                        text_color="black",
                        background_color="red")
            ]

    layout = [
        status_layout,
        [sg.HorizontalSeparator()],
        [
            sg.Text('Color Temperature:'),
            sg.Combo(['D65', 'D75', 'TL84', 'INCA'], size=(20, 20),
                     key='selected_color_temp',
                     default_value='D65',
                     enable_events=True),
        ],
        [
            sg.Text(text='Switch light (2-5 are only for INCA)'),
            sg.Combo(['all', '0', '1', '2', '3', '4', '5'], size=(20, 20),
                     key='selected_light_num',
                     default_value='all',
                     enable_events=True),
            sg.Button('Turn on', button_color=(sg.theme_text_element_background_color(), 'silver'), size=(10, 2),
                      key='on_1_btn', disabled=False),
            sg.Button('Turn off', button_color=(sg.theme_text_element_background_color(), 'silver'), size=(10, 2),
                      key='off_1_btn', disabled=False)
        ],
        [
            sg.Text(text='Set Brightness'),
            sg.Slider(range=(1, 100), orientation='h', key='selected_brightness'),
            sg.Button('Set', button_color=(sg.theme_text_element_background_color(), 'silver'), size=(10, 2),
                      key='set_brightness_btn', disabled=False)
        ],
        [sg.Button('Party', button_color=(sg.theme_text_element_background_color(), 'silver'), size=(10, 2),
                   key='send_settings_btn', disabled=False)]
    ]

    # Create the Window
    window = sg.Window('Lights Test', layout,
                       icon=os.path.join(ROOT_DIR, 'images', 'automated-video-testing-header-icon.ico'))

    lights = LightsCtrl(selected_lights_model)  # Create object

    lights_status = lights.status()

    while True:
        event, values = window.read(200)

        if event == sg.WIN_CLOSED or event == 'Close':  # if user closes window or clicks cancel
            break

        window['is-connected-0-relay'].Update(
            "Connected" if lights_status[0]['relay'] else "Not Connected",
            background_color='green' if lights_status[0]['relay'] else 'red'),
        window['is-connected-0-dimmer'].Update(
            "Connected" if lights_status[0]['dimmer'] else "Not Connected",
            background_color='green' if lights_status[0]['dimmer'] else 'red'),
        window['is-connected-1-relay'].Update(
            "Connected" if lights_status[1]['relay'] else "Not Connected",
            background_color='green' if lights_status[1]['relay'] else 'red'),
        window['is-connected-1-dimmer'].Update(
            "Connected" if lights_status[1]['dimmer'] else "Not Connected",
            background_color='green' if lights_status[1]['dimmer'] else 'red')


        print('vals', values)  # Debugging
        print('event', event)  # Debugging

        if event == 'send_settings_btn':
            print("Selected light ", selected_lights_model)
            lights.make_a_party()

        if event == 'on_1_btn':
            if values['selected_light_num'] != '':
                lights.turn_on(values['selected_color_temp'], values['selected_light_num'])
            else:
                lights.turn_on(values['selected_color_temp'])

        if event == 'off_1_btn':
            if values['selected_light_num'] != '':
                lights.turn_off(values['selected_color_temp'], values['selected_light_num'])
            else:
                lights.turn_off(values['selected_color_temp'])

        if event == 'set_brightness_btn':
            lights.set_brightness(values['selected_brightness'])
            pass

    window.close()
    lights.disconnect()
