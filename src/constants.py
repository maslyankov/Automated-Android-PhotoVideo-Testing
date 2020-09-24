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
act_sequences = {
    'photo': 'shoot_photo_seq',
    'video': 'shoot_video_seq',
    'goto_photo': 'goto_photo_seq',
    'goto_video': 'goto_video_seq'
}

act_sequences_desc = {
    'photo': 'Shoot Photo',
    'video': 'Shoot Video',
    'goto_photo': 'Change Mode to Photo',
    'goto_video': 'Change Mode to Video'
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

