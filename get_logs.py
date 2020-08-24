import subprocess, os, sys, time, signal

class DeviceLogs:
    def start_logs(self, gr_filter, logfile):
        self.flog = open(logfile, "w")


        print("Getting logs...")
        self.plogcat0 = subprocess.Popen(["adb", "logcat","-G","100M"])

        self.plogcat1 = subprocess.Popen(["adb", "logcat"],
                             stdout=subprocess.PIPE,
                             env=os.environ
                             )  # Todo -> route output to a pipe in order to separate grep from this
                                                                                                                # https://pymotw.com/2/subprocess/
        self.pgrep = subprocess.Popen(['grep', gr_filter],
                                stdin=self.plogcat1.stdout,
                                stdout=self.flog,
                                )

        # do some other operations

    def stop_logs(self):
        # Stop Logs
        self.plogcat0.terminate()
        self.plogcat1.terminate()
        self.pgrep.terminate()
        self.flog.close()
