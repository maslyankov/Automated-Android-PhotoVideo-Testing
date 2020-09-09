## Original file - https://github.com/tzutalin/adb-event-record/blob/master/adbrecord.py
import os
import subprocess
from subprocess import PIPE
import re
import time

ELEVATED = False



def grabScreenResolution(udid):
    adb = subprocess.Popen(('adb', '-s', udid, 'shell', 'dumpsys', 'window'), stdout=subprocess.PIPE) #  | grep "mUnrestricted"'
    output = subprocess.Popen(['grep', 'mUnrestricted'],
                                     stdin=adb.stdout,
                                     stdout=subprocess.PIPE)
    out = re.findall("\d+", str(output.stdout.read()))
    return [out[2],out[3]]


def GrabUiAutomator(udid):
    saved_file = '.\\XML\\' + str(udid) + '.xml'
    command = "adb -s {} shell uiautomator dump && adb -s {} pull /sdcard/window_dump.xml {}".format(
        udid, udid, saved_file)
    print(command)
    runCommand(command)
    return saved_file


def main():
    # print(str(GrabUiAutomator("cf108b7")))
    #print(grabScreenResolution("cf108b7"))
    print("Hi")


if __name__ == "__main__":
    main()
