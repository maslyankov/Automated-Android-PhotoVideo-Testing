from actions import *
from get_logs import DeviceLogs
from device import Device
import time


def main():
    device = Device()
    dlogs = DeviceLogs()



    # shoot_video(device, 5)

    device.open_snap_cam()
    device.take_photo()
    #dlogs.start_logs("Gain:ExpTime", "logfile.txt")
    #shoot_video(device, 10)
    #dlogs.stop_logs()

    #device.push_file("tuning/com.qti.tuned.snap_imx476.bin", "vendor/lib/camera")
    #device.pull_file("sdcard/DCIM/Camera/IMG_20200804_152412.jpg", "./tests1/IMG_20200804_152412.jpg")

    time.sleep(1)
    pull_camera_files(device, "tests2", True)


if __name__ == "__main__":
    main()
