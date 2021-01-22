import os
import sys
from pathlib import Path

# Directories
# determine if application is a script file or frozen exe
if getattr(sys, 'frozen', False):
    DEBUG_MODE = False

    EXE_PATH = os.path.dirname(sys.executable)
    SETTINGS_DIR = os.path.join(EXE_PATH, 'settings')

    ROOT_DIR = sys._MEIPASS
else:
    DEBUG_MODE = True

    ROOT_DIR = os.path.abspath(os.curdir + "/../")  # This is Project Root
    SETTINGS_DIR = os.path.join(ROOT_DIR, 'settings')

DEVICES_SETTINGS_DIR = os.path.join(SETTINGS_DIR, 'devices')
DATA_DIR = os.path.join(ROOT_DIR, 'data')
TMP_DIR = os.path.join(ROOT_DIR, 'temp')
XML_DIR = os.path.join(TMP_DIR, 'XML')
VENDOR_DIR = os.path.join(ROOT_DIR, 'vendor')
# Create dirs if not exist
Path(DEVICES_SETTINGS_DIR).mkdir(parents=True, exist_ok=True)
Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
Path(XML_DIR).mkdir(parents=True, exist_ok=True)

ADB = os.path.join(VENDOR_DIR, 'scrcpy-win64-v1.17', 'adb.exe')
SCRCPY = os.path.join(VENDOR_DIR, 'scrcpy-win64-v1.17', 'scrcpy.exe')


# Logs settings
LOG_FILE = 'ac_debug.log'
LOG_LEVEL = 'DEBUG'
LOG_LEVEL_FILE = 'DEBUG'


# Settings
MAX_DEVICES_AT_ONE_RUN = 6
MAX_ACTIONS_DISPLAY = 5

APP_VERSION = '0.12 Beta'

# - Actions - #

# Action types
ACT_SEQUENCES = {
    'goto_photo': 'goto_photo_seq',
    'photo': 'shoot_photo_seq',
    'goto_video': 'goto_video_seq',
    'video_start': 'start_video_seq',
    'video_stop': 'stop_video_seq'
}

ACT_SEQUENCES_DESC = {
    'goto_photo': 'Change Mode to Photo',
    'photo': 'Shoot Photo',
    'goto_video': 'Change Mode to Video',
    'video_start': 'Start Shooting Video',
    'video_stop': 'Stop Shooting Video'
}

# Custom actions
CUSTOM_ACTIONS = [  # TODO: Add swipe left, right, etc
    'Empty',
    'delay'
]

# Lights
LIGHTS_MODELS = {
    'SpectriWave': 1,
    'lightStudio': 2
}

AVAILABLE_LIGHTS = {
    1: ['D65', 'D75', 'TL84', 'INCA'],
    2: []
}

# LUXMETERS
LUXMETERS_MODELS = {
    'Konita Minolta CL-200A': 1
}

# Light Temperatures
KELVINS_TABLE = {
    "LED_3000": (3000, 'Light Emitting Diode'),
    "LED_5000": (5000, 'Light Emitting Diode'),
    "LED_6000": (6000, 'Light Emitting Diode'),
    "E27-Warm": (2700, 'Same as WW'),
    "E27 Cool": (5000, ''),
    "CFL":      (3500, 'Cool Flourescent Lights, same as TL835'),
    "INCA":     (2400, 'Standard Incandescent lamps'),
    "INCA2":    (2550, 'Soft white Incandescent lamps'),
    "WW":       (2700, 'Warm White'),
    "A":        (2856, 'Incandescent - typical, domestic, tungsten-filament lighting'),
    "TL83":     (3000, 'Warm white fluorescent'),
    "TL835":    (3500, 'Fluorescent narrow tri-band'),
    "TL84":     (4000, 'Warm White Fluorescent'),
    "CWF":      (4230, 'Cool white fluorescent'),
    "D50":      (5003, '"horizon" light'),
    "D55":      (5500, 'Mid-afternoon Daylight'),
    "D65":      (6504, 'Noon Daylight, broad-band fluorescent lamp'),
    "C":        (6770, 'Overcast sky'),
    "D75":      (7500, 'North sky Daylight')
}

# Filetypes
EXCEL_FILETYPES = [
    'xls', 'xlsx', 'xlsm', 'xltx', 'xltm'
]

# Imatest
IMATEST_PARALLEL_TEST_TYPES = {
    'blemish': 'BLEMISH_ANALYSIS',
    'checkerboard': 'CHECKERBOARD_ANALYSIS',
    'colorcheck': 'COLORCHECK_ANALYSIS',
    'distortion': 'DISTORTION_ANALYSIS',
    'dotpattern': 'DOTPATTERN_ANALYSIS',
    'esfriso': 'ESFRISO_ANALYSIS',
    'colortone': 'COLOR_TONE_ANALYSIS',
    'random': 'RANDOM_ANALYSIS',
    'sfr': 'SFR_ANALYSIS',
    'sfrplus': 'SFRPLUS_ANALYSIS',
    'sfrreg': 'SFRREG_ANALYSIS',
    'star': 'STAR_ANALYSIS',
    'uniformity': 'UNIFORMITY_ANALYSIS',
    'wedge': 'WEDGE_ANALYSIS'
}

IMATEST_TEST_TYPES = {
    'sfr': 'sfr_json',
    'sfrplus': 'sfrplus_json',
    'star': 'star_json',
    'colorcheck': 'colorcheck_json',
    'stepchart': 'stepchart_json',
    'wedge': 'wedge_json',
    'uniformity': 'uniformity_json',
    'distortion': 'distortion_json',
    'esfriso': 'esfriso_json',
    'blemish': 'blemish_json',
    'dotpattern': 'dotpattern_json',
    'colortone': 'color_tone_json',
    'checkerboard': 'checkerboard_json',
    'random': 'random_json',
    'sfrreg': 'sfrreg_json',
    'logfc': 'logfc_json'
}

IMATEST_TEST_TYPES_FRIENDLY = {
    'blemish': 'Blemish',
    'checkerboard': 'Checkerboard',
    'colorcheck': 'Colorcheck',
    'distortion': 'Distortion',
    'dotpattern': 'Dotpattern',
    'esfriso': 'eSFR ISO',
    'colortone': 'Color/Tone',
    'random': 'Random',
    'sfr': 'SFR',
    'sfrplus': 'SFRPlus',
    'sfrreg': 'SFR Reg',
    'star': 'Star',
    'uniformity': 'Uniformity',
    'wedge': 'Wedge',
    'logfc': 'LogFC',
    'stepchart': 'Stepchart',
}

# DEBUG
if DEBUG_MODE:
    LIGHTS_MODELS['test'] = 0
    AVAILABLE_LIGHTS[0] = ['D65', 'D75', 'TL84', 'INCA']
    LUXMETERS_MODELS['test'] = 0

# Main Colors
TEXT_COLOR = '#aaaaaa'
DARK_COLOR = '#181818'
MID_COLOR = '#cccccc'
BUTTON_TEXT_COLOR = '#FFFFFF'
ALTERNATE_COLOR = '#ff7700'
PRIMARY_COLOR = '#ff8800'

# GUI Visual Settings
GUI_BG_COLOR = DARK_COLOR
GUI_TEXT_COLOR = TEXT_COLOR

GUI_INPUT_BG_COLOR = MID_COLOR
GUI_INPUT_TEXT_COLOR = DARK_COLOR

GUI_BORDER_WIDTH = 0

GUI_BUTTON_TEXT_COLOR = BUTTON_TEXT_COLOR
GUI_BUTTON_BG_COLOR = ALTERNATE_COLOR

GUI_PROGRESS_BAR_COLOR = PRIMARY_COLOR
GUI_PROGRESS_BAR_BORDER_WIDTH = 0

GUI_SLIDER_COLOR = PRIMARY_COLOR

GUI_ELEMENT_BG_COLOR = DARK_COLOR
GUI_ELEMENT_TEXT_COLOR = TEXT_COLOR

# GUI Icons
FOLDER_ICON = b'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAACXBIWXMAAAsSAAALEgHS3X78AAABnUlEQVQ4y8WSv2rUQRSFv7vZgJFFsQg2EkWb4AvEJ8hqKVilSmFn3iNvIAp21oIW9haihBRKiqwElMVsIJjNrprsOr/5dyzml3UhEQIWHhjmcpn7zblw4B9lJ8Xag9mlmQb3AJzX3tOX8Tngzg349q7t5xcfzpKGhOFHnjx+9qLTzW8wsmFTL2Gzk7Y2O/k9kCbtwUZbV+Zvo8Md3PALrjoiqsKSR9ljpAJpwOsNtlfXfRvoNU8Arr/NsVo0ry5z4dZN5hoGqEzYDChBOoKwS/vSq0XW3y5NAI/uN1cvLqzQur4MCpBGEEd1PQDfQ74HYR+LfeQOAOYAmgAmbly+dgfid5CHPIKqC74L8RDyGPIYy7+QQjFWa7ICsQ8SpB/IfcJSDVMAJUwJkYDMNOEPIBxA/gnuMyYPijXAI3lMse7FGnIKsIuqrxgRSeXOoYZUCI8pIKW/OHA7kD2YYcpAKgM5ABXk4qSsdJaDOMCsgTIYAlL5TQFTyUIZDmev0N/bnwqnylEBQS45UKnHx/lUlFvA3fo+jwR8ALb47/oNma38cuqiJ9AAAAAASUVORK5CYII='
FILE_ICON = b'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAACXBIWXMAAAsSAAALEgHS3X78AAABU0lEQVQ4y52TzStEURiHn/ecc6XG54JSdlMkNhYWsiILS0lsJaUsLW2Mv8CfIDtr2VtbY4GUEvmIZnKbZsY977Uwt2HcyW1+dTZvt6fn9557BGB+aaNQKBR2ifkbgWR+cX13ubO1svz++niVTA1ArDHDg91UahHFsMxbKWycYsjze4muTsP64vT43v7hSf/A0FgdjQPQWAmco68nB+T+SFSqNUQgcIbN1bn8Z3RwvL22MAvcu8TACFgrpMVZ4aUYcn77BMDkxGgemAGOHIBXxRjBWZMKoCPA2h6qEUSRR2MF6GxUUMUaIUgBCNTnAcm3H2G5YQfgvccYIXAtDH7FoKq/AaqKlbrBj2trFVXfBPAea4SOIIsBeN9kkCwxsNkAqRWy7+B7Z00G3xVc2wZeMSI4S7sVYkSk5Z/4PyBWROqvox3A28PN2cjUwinQC9QyckKALxj4kv2auK0xAAAAAElFTkSuQmCC'

SYMBOL_UP =    '▲'
SYMBOL_DOWN =  '▼'

# Device Icons
DEVICE_ICONS = {
    'android': os.path.join(ROOT_DIR, 'images', 'device-icons', 'android-flat-32.png'),
    'linux': os.path.join(ROOT_DIR, 'images', 'device-icons', 'linux-32.png'),
    'usb_cam': os.path.join(ROOT_DIR, 'images', 'device-icons', 'usb-circular-32.png')
}

#SCRCPY NO WINDOW MASK
CREATE_NO_WINDOW = 0x08000000
