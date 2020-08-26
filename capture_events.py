## Original file - https://github.com/tzutalin/adb-event-record/blob/master/adbrecord.py

import subprocess
from subprocess import PIPE
import re
import time

EVENT_LINE_RE = re.compile(r"(\S+): (\S+) (\S+) (\S+)$")
STORE_LINE_RE = re.compile(r"(\S+) (\S+) (\S+) (\S+) (\S+)$")

def dlog(msg):
    print(str(msg))

class CaptureEvents():

    def record(self, fpath, eventNum=None):
        print('Start recording')
        record_command = self.adb_shell_command + [b'getevent']
        adb = subprocess.Popen(record_command,
                               stdin=PIPE, stdout=PIPE,
                               stderr=PIPE)

        outputFile = open(fpath, 'w')
        while adb.poll() is None:
            try:
                millis = int(round(time.time() * 1000))
                line = adb.stdout.readline().decode('utf-8', 'replace').strip()
                match = EVENT_LINE_RE.match(line.strip())
                if match is not None:
                    dev, etype, ecode, data = match.groups()
                    ## Filter event
                    if eventNum is not None and '/dev/input/event%s' % (eventNum) != dev:
                        continue
                    ## Write to the file
                    etype, ecode, data = int(etype, 16), int(ecode, 16), int(data, 16)
                    rline = "%s %s %s %s %s\n" % (millis, dev, etype, ecode, data)
                    dlog(rline)
                    outputFile.write(rline)
            except KeyboardInterrupt:
                break
            if len(line) == 0:
                break
        outputFile.close()
        print('End recording')

    def play(self, fpath, repeat=False):
        print('Start playing')
        while True:
            lastTs = None
            with open(fpath) as fp:
                for line in fp:
                    match = STORE_LINE_RE.match(line.strip())
                    ts, dev, etype, ecode, data = match.groups()
                    ts = float(ts)
                    if lastTs and (ts - lastTs) > 0:
                        delta_second = (ts - lastTs) / 1000
                        time.sleep(delta_second)

                    lastTs = ts
                    cmds = self.adb_shell_command + [b'sendevent', dev, etype, ecode, data]
                    dlog(cmds)
                    if subprocess.call(cmds) != 0:
                        raise OSError('sendevent failed')

            if repeat == False:
                break
        print('End playing')