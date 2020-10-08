import os

# Directories
ROOT_DIR = os.path.abspath(os.curdir + "/../")  # This is Project Root
ADB = os.path.join(ROOT_DIR, 'vendor', 'scrcpy-win64-v1.16', 'adb.exe')
SCRCPY = os.path.join(ROOT_DIR, 'vendor', 'scrcpy-win64-v1.16', 'scrcpy.exe')

# Settings
MAX_DEVICES_AT_ONE_RUN = 6
MAX_ACTIONS_DISPLAY = 5

APP_VERSION = '0.01 Beta'

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
CUSTOM_ACTIONS = [
    'Empty',
    'delay'
]

# Lights
LIGHTS_MODELS = {
    'SpectriWave': 0,
    'lightStudio': 1
}

AVAILABLE_LIGHTS = {
    'SpectriWave': ['D65', 'D75', 'TL84', 'INCA'],
    'lightStudio': []
}

# Light Temperatures
KELVINS_TABLE = {
    "WW":       (2700, 'Warm White'),
    "A":        (2856, 'Incandescent - typical, domestic, tungsten-filament lighting'),
    "TL83":     (3000, 'Warm white fluorescent'),
    "TL835":    (3500, 'Fluorescent narrow tri-band'),
    "TL84":     (4100, 'Warm White Fluorescent'),
    "CWF":      (4230, 'Cool white fluorescent'),
    "D50":      (5000, '"horizon" light'),
    "D55":      (5500, 'Mid-afternoon Daylight'),
    "D65":      (6500, 'Noon Daylight'),
    "C":        (6770, 'Overcast sky'),
    "D75":      (7500, 'North sky Daylight')
}