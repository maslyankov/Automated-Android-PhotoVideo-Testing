from setuptools import setup
import sys
from cx_Freeze import setup, Executable


build_exe_options = {}

# GUI applications require a different base on Windows (the default is for a
# console application).
base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(
    name='automated_cases',
    version='0.18',
    packages=[''],
    url='',
    license='',
    author='Martin Maslyankov',
    author_email='m.maslyankov@me.com',
    description='Tool for automating the creation of test cases for image recording devices',
    options = {"build_exe": build_exe_options},
    executables = [Executable("src/run_app.py", base=base)]
)
