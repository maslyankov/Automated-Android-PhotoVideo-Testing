import time


def shoot_video(obj, duration=10, with_logs=False, logs_filter="", logs_file=""):
    print("Starting Video...")
    obj.start_video()

    if with_logs:
        # Logs
        dlogs = DeviceLogs()
        dlogs.start_logs(logs_filter, logs_file)

    print("Waiting {} secs".format(duration))
    time.sleep(duration)

    print("Ending video")
    obj.stop_video()

    if with_logs:
        # Logs
        dlogs.stop_logs()


def shoot_photo(obj, with_logs=False, logs_filter="", logs_file=""):
    print("Shooting a Photo...")

    if with_logs:
        # Logs
        dlogs = DeviceLogs()
        dlogs.start_logs(logs_filter, logs_file)

    obj.take_photo()

    if with_logs:
        # Logs
        dlogs.stop_logs()


def pull_camera_files(obj, folder, clear_after_pull):
    files_list = obj.get_camera_files_list()

    if files_list != None:
        print(files_list)
        for num, file in enumerate(files_list):
            num += 1;  # So we don't start from 0
            print("Pulling file No {}: {}".format(str(num), file) +  " -> ./{}/case{}.{}".format(folder, str(num), file.split(".")[-1]) )
            obj.pull_file("sdcard/DCIM/Camera/" + file, "{}/case{}.{}".format(folder, str(num), file.split(".")[-1]))

        if clear_after_pull:
            obj.clear_camera_folder()
