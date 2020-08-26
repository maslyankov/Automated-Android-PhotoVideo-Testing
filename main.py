from gui import gui
from device import Device

def main():
    #device = Device('cf108b7')

    # shoot_video(device, 5)
    # device.open_snap_cam()
    # device.take_photo()
    # shoot_video(device, 10, True, "Gain:ExpTime", "logfile.txt")
    # device.push_file("tuning/com.qti.tuned.snap_imx476.bin", "vendor/lib/camera/com.qti.tuned.snap_imx476.bin")
    # device.push_file(r'.\tmp\camxoverridesettings_new.txt', 'vendor/etc/camera/camxoverridesettings2.txt')
    # pull_camera_files(device, "tests2", True)

    gui()


if __name__ == "__main__":
    main()
