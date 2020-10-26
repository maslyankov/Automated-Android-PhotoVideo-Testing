set exe_name="MM-Automations-App"
set app_version="0-02-Beta"

python -m PyInstaller --add-data "vendor;vendor" --add-data "data;data" --add-data "images;images" --name "%exe_name%_%app_version%" --noupx --noconsole --onefile -i ./images/automated-video-testing-header-icon.ico ./automated_cases.py
python -m PyInstaller --add-data "vendor;vendor" --add-data "data;data" --add-data "images;images" --name "%exe_name%_%app_version%_console" --noupx --onefile -i ./images/automated-video-testing-header-icon.ico ./automated_cases.py