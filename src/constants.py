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
    print('App not build to an exe. Setting DEBUG_MODE on')
    DEBUG_MODE = True

    ROOT_DIR = os.path.abspath(os.curdir + "/../")  # This is Project Root
    SETTINGS_DIR = os.path.join(ROOT_DIR, 'settings')

DEVICES_SETTINGS_DIR = os.path.join(SETTINGS_DIR, 'devices')
TMP_DIR = os.path.join(ROOT_DIR, 'temp')
XML_DIR = os.path.join(TMP_DIR, 'XML')
# Create dirs if not exist
Path(DEVICES_SETTINGS_DIR).mkdir(parents=True, exist_ok=True)
Path(XML_DIR).mkdir(parents=True, exist_ok=True)

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
    "INCA1":    (2400, 'Standard Incandescent lamps'),
    "INCA2":    (2550, 'Soft white Incandescent lamps'),
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

# Imatest
IMATEST_TEST_TYPES = {
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

IMATEST_TEST_TYPES_CALLS = {

}

# DEBUG
if DEBUG_MODE:
    LIGHTS_MODELS['test'] = 0
    AVAILABLE_LIGHTS[0] = ['D65', 'D75', 'TL84', 'INCA']
    LUXMETERS_MODELS['test'] = 0
