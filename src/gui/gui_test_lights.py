import os
import time
import PySimpleGUI as sg
from src.app.LightsCtrl import LightsCtrl
from src.konica.ChromaMeterKonica import ChromaMeterKonica

import src.constants as constants


def gui_test_lights(selected_lights_model, selected_luxmeter_model):
    lights = LightsCtrl(selected_lights_model)  # Create object

    if selected_lights_model == 'SpectriWave':
        lights_header_image = [
            sg.Image(os.path.join(constants.ROOT_DIR, 'vendor', 'wireless_lighting', 'spectriwave.png'))
        ]

        status_frame = [[
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
        ],
            [sg.HorizontalSeparator()],
        [
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
                        background_color="red"),
        ],
        ]
    else:
        lights_header_image = []
        status_frame = [[]]

    luxmeter_frame = [
        [sg.Text('Luxmeter', font='Any 18', key='luxmeter_name', size=(20, 1), auto_size_text=True)],
        [sg.Text('Loading..', key='luxmeter_lux_value', font='Any 17', text_color='red', auto_size_text=True)],
        [sg.HorizontalSeparator()],
        [sg.Input(key='target_lux'), sg.Button("Set Lights to this LUX value", key='set_target_lux_btn')]
    ]

    layout = [
        lights_header_image,
        [sg.Frame('Status', status_frame, font='Any 12', title_color='white')],
        [sg.HorizontalSeparator()],
        [
            sg.Text('Color Temperature:'),
            sg.Combo(lights.available_lights, size=(20, 20),
                     key='selected_color_temp',
                     default_value=lights.available_lights[0] if lights.available_lights else '',
                     enable_events=True),
        ],
        [
            sg.Text(text='Switch light (2-5 are only for INCA)'),
            sg.Combo(['all', '0', '1', '2'], size=(20, 20),
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
        [
            sg.Frame('Luxmeter', luxmeter_frame, font='Any 12', title_color='white', visible=False if selected_luxmeter_model == 'None' else True),
            sg.Button('Party',
                   button_color=(sg.theme_text_element_background_color(), 'silver'),
                   size=(10, 2),
                   key='send_settings_btn', disabled=False)]
    ]

    # Create the Window
    window = sg.Window('Lights Test', layout,
                       icon=os.path.join(constants.ROOT_DIR, 'images', 'automated-video-testing-header-icon.ico'))

    if selected_lights_model == 'SpectriWave':  # SpectriWave Specific
        time.sleep(1)
        lights_status = lights.status()

    if selected_luxmeter_model == 'Konita Minolta CL-200A': # Konita Minolta CL-200A Selected
        print("Initializing Luxmeter...")
        luxmeter = ChromaMeterKonica()

    while True:
        event, values = window.read(600)

        if event == sg.WIN_CLOSED or event == 'Close':  # if user closes window or clicks cancel
            break

        if selected_lights_model == 'SpectriWave':  # SpectriWave Specific
            if not lights_status[0]['relay']:
                print("Checking again for status...")
                # lights_status = lights.status()

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

            if event == 'selected_color_temp' and values['selected_color_temp'] == 'INCA':
                window['selected_light_num'].Update(values=['all', '0', '1', '2', '3', '4', '5'])
            elif event == 'selected_color_temp':
                window['selected_light_num'].Update(values=['all', '0', '1', '2'])

        if selected_luxmeter_model == 'Konita Minolta CL-200A':  # Konita Minolta CL-200A Selected
            if luxmeter.is_alive:
                window['luxmeter_name'].Update('Konita Minolta CL-200A')
                window['luxmeter_lux_value'].Update(str(luxmeter.get_lux()))
            else:
                window['luxmeter_lux_value'].Update("Connection Lost")

        print('vals', values)  # Debugging
        print('event', event)  # Debugging

        if event == 'send_settings_btn':
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

        if event == 'set_target_lux_btn':
            lights.set_lux(luxmeter, int(values['target_lux']))

    window.close()
    lights.disconnect()
