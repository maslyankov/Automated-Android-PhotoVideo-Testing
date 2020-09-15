import os
import PySimpleGUI as sg
from src.app.LightsCtrl import LightsCtrl

ROOT_DIR = os.path.abspath(os.curdir + "/../")  # This is Project Root


def gui_test_lights(selected_lights_model):
    lights = LightsCtrl(selected_lights_model)

    layout = [
        [
            sg.Combo(['D65', 'D75', 'TL84', 'INCA'], size=(20, 20),
                     key='selected_color_temp',
                     default_value='D65',
                     enable_events=True),
            sg.Text(text='Connected', key='is-connected')
        ],
        [
            sg.Text(text='Switch light (2-5 are only for INCA)'),
            sg.Combo(['all', '0', '1', '2', '3', '4', '5'], size=(20, 20),
                     key='selected_light_num',
                     default_value='',
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

    while True:
        event, values = window.read()

        if event == sg.WIN_CLOSED or event == 'Close':  # if user closes window or clicks cancel
            break

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
