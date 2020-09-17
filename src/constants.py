import os

# Directories
ROOT_DIR = os.path.abspath(os.curdir + "/../")  # This is Project Root
ADB = os.path.join(ROOT_DIR, 'vendor', 'scrcpy-win64-v1.16', 'adb.exe')
SCRCPY = os.path.join(ROOT_DIR, 'vendor', 'scrcpy-win64-v1.16', 'scrcpy.exe')

# Settings
MAX_DEVICES_AT_ONE_RUN = 6

APP_VERSION = '0.01 Beta'

# Lights
LIGHTS_MODELS = {
    'SpectriWave': 0,
    'lightStudio': 1
}