import xml.etree.cElementTree as ET
from subprocess import Popen, PIPE
from time import sleep
from re import findall
from os import path, kill
from signal import CTRL_C_EVENT, SIGINT
from datetime import datetime
from natsort import natsorted

from src.base.devices.Device import Device
from src.base.utils.xml_tools import generate_sequence, xml_from_sequence

from src import constants
from src.logs import logger


# ---------- CLASS ADBDevice ----------
class ADBDevice(Device):
    """
    Class for interacting with devices using adb (ppadb) and AdbClient class
    """

    # ----- INITIALIZER -----
    def __init__(self, adb, device_serial):
        super().__init__(
            serial=device_serial,  # Assign device serial as received in arguments
        )

        # Object Parameters #
        self.scrcpy = []

        # Settings
        self.camera_app = None

        # States
        self.current_camera_app_mode = 'photo'

        # Sequences
        self.shoot_photo_seq = []
        self.start_video_seq = []
        self.stop_video_seq = []
        self.goto_photo_seq = []
        self.goto_video_seq = []
        self.actions_time_gap = 1

        # Persistence
        self.adb = adb

        self.root()  # Make sure we are using root for device

        self.d = self.adb.client.device(device_serial)  # Create device client object

        try:
            self.friendly_name = self.get_device_model()
            android_ver_response = self.get_android_version()
            self.android_ver = int(android_ver_response.split('.')[0]) if android_ver_response else None
        except RuntimeError:
            logger.error("Device went offline!")
        except ValueError as e:
            logger.error(e)

        # TODO: Move to parent class
        self.load_settings_file()

        self.print_attributes()

        self.setup_device_settings()
        self.turn_on_and_unlock()

    # ----- Base methods -----
    def root(self):
        """
        Root the device
        :return:None
        """
        logger.info(f"Rooting device {self.device_serial}")
        self.adb.anticipate_root = True
        CREATE_NO_WINDOW = 0x08000000
        root = Popen([constants.ADB, '-s', self.device_serial, 'root'],
                     stdin=PIPE,
                     stdout=PIPE,
                     stderr=PIPE,
                     creationflags=CREATE_NO_WINDOW)
        root.stdin.close()
        stdout, stderr = root.communicate()
        if stderr:
            try:
                if b"unauthorized" in stderr:
                    raise ValueError(
                        f"Device not rooted (probably) or you didn't allow usb debugging.\nRooting Errors: {stderr.decode()}")
                else:
                    raise ValueError(f'Rooting Errors: {stderr.decode()}')
            except ValueError as e:
                logger.critical(e)
        if stdout:
            logger.info("Rooting Output: {}".format(stdout.decode()))
        root.terminate()

    def remount(self):
        """
        Remount the device
        :return:None
        """
        logger.info(f"Remount device serial: {self.device_serial}")
        CREATE_NO_WINDOW = 0x08000000
        remount = Popen([constants.ADB, '-s', self.device_serial, 'remount'],
                        stdin=PIPE,
                        stdout=PIPE,
                        stderr=PIPE,
                        creationflags=CREATE_NO_WINDOW)
        remount.stdin.close()
        stdout, stderr = remount.communicate()
        if stderr:
            logger.error("Remount Errors: ".format(stderr.decode()))
        if stdout:
            logger.warn("Remount Output: ".format(stdout.decode()))
        remount.terminate()

    def disable_verity(self):
        """
        Disabled verity of device
        :return:None
        """
        print("Dis verity device serial: " + self.device_serial)
        CREATE_NO_WINDOW = 0x08000000
        self.adb.anticipate_root = True
        disver = Popen([constants.ADB, '-s', self.device_serial, 'disable-verity'],
                       stdin=PIPE,
                       stdout=PIPE,
                       stderr=PIPE,
                       creationflags=CREATE_NO_WINDOW)
        disver.stdin.close()
        stdout, stderr = disver.communicate()
        if stderr:
            logger.error("Dis verity Errors: ".format(stderr.decode()))
        if stdout:
            logger.warn("Dis verity Output: ".format(stdout.decode()))
        disver.terminate()

        logger.info('Rebooting device after disabling verity!')
        self.reboot()

    def exec_shell(self, cmd):
        """
        Execute a shell command on the device
        :param cmd:String command to execute
        :return:None
        """
        try:
            logger.debug(f'executing {cmd}')
            return self.d.shell(cmd)
        except AttributeError as e:
            logger.exception('You tried to reach a device that is already disconnected!')
            quit(1)
        except RuntimeError as e:
            logger.error('Device Disconnected unexpectedly! Detaching...')
            self.detach_device()

    def push_file(self, src, dst):
        """
        Push file to device
        :param src: Path to file to push
        :param dst: Destination on device of file
        :return:None
        """
        logger.debug(f'Pushing {src} to {dst}')
        self.d.push(src, dst)

    def pull_file(self, src, dst):
        """
        Pull file to device
        :param src: Path on device to file to pull
        :param dst: Destination to save the file to
        :return:None
        """
        logger.debug(f'Pulling {src} into {dst}')  # Debugging
        self.d.pull(src, dst)

    def detach_device(self):
        self.adb.detach_device(self.device_serial)

    # ----- Getters/Setters -----
    def set_shoot_photo_seq(self, seq):
        self.shoot_photo_seq = seq

    def get_shoot_photo_seq(self):
        return self.shoot_photo_seq

    def set_start_video_seq(self, seq):
        self.start_video_seq = seq

    def get_start_video_seq(self):
        return self.start_video_seq

    def set_stop_video_seq(self, seq):
        self.stop_video_seq = seq

    def get_stop_video_seq(self):
        return self.stop_video_seq

    def set_camera_app_pkg(self, pkg):
        self.camera_app = pkg

    def get_camera_app_pkg(self):
        return self.camera_app

    # ----- Getters -----
    def get_device_model(self):
        """
        Get the device model
        :return: String of device model
        """
        response = self.exec_shell("getprop ro.product.model")
        return response.strip() if response else None

    def get_device_name(self):
        """
        Get the device name
        :return: String of device name
        """
        response = self.exec_shell("getprop ro.product.name")
        return response.strip() if response else None

    def get_manufacturer(self):
        return self.exec_shell("getprop ro.product.manufacturer").strip()

    def get_board(self):
        response = self.exec_shell("getprop ro.product.board")
        return response.strip() if response else None

    def get_android_version(self):
        response = self.exec_shell("getprop ro.build.version.release")
        return response.strip() if response else None

    def get_sdk_version(self):
        response = self.exec_shell("getprop ro.build.version.sdk")
        return response.strip() if response else None

    def get_cpu(self):
        response = self.exec_shell("getprop ro.product.cpu.abi")
        return response.strip() if response else None

    def get_current_app(self):
        """
        Returns currently opened app package and its current activity
        :return:None
        """
        # dumpsys window windows | grep -E 'mFocusedApp' <- had issues with this one, sometimes returns null
        # Alternative -> dumpsys activity | grep top-activity
        # First try
        try:  # This works on older Android versions
            current = self.exec_shell("dumpsys activity | grep -E 'mFocusedActivity'").strip().split(' ')[3].split('/')
            if current is None:
                logger.debug('(Get Current App) Focused Activity is empty, trying top-activity...')
                current = self.exec_shell("dumpsys activity | grep top-activity").strip().split(' ')[9].split(':')
                temp = current[1].split('/')
                temp.append(current[0])  # -> [pkg, activity_id, pid]
                return temp
        except IndexError:
            pass
        else:
            return current

        # Second try
        try:
            current = self.exec_shell("dumpsys window windows | grep -E 'mFocusedApp'").split(' ')[6].split('/')
        except IndexError:
            pass
        else:
            return current

        # Third try
        try:
            current = self.exec_shell("dumpsys window windows | grep -E 'ActivityRecord'").split(' ')[13].split('/')
        except IndexError:
            pass
        else:
            logger.debug(f"Current app: {current}")
            return current
        # else
        logger.error("Can't fetch currently opened app! \nOutput of dumpsys: ")

        logger.error(self.exec_shell("dumpsys window windows"))
        return None

    def get_installed_packages(self):
        """
        Get the packages (apps) installed on device
        pm list packages - more widely available than:
        'cmd package list packages -e'
        :return:List of strings, each being an app package on the device
        """
        return sorted(self.exec_shell("pm list packages").replace('package:', '').splitlines())

    def get_recursive_files_list(self, target_dir):
        files_list = self.exec_shell(f"ls -R {target_dir}").splitlines()

        return files_list
        # for num, f in enumerate(files_list):
        #     files_list[num] = f.split()

    def get_files_and_folders(self, target_dir):
        files_list = self.exec_shell(f"ls -l {target_dir}").splitlines()
        # links: lrwxrwxrwx root     root              1970-01-01 02:00 fg_algo_cos -> /sbin/fg_algo_cos
        # folders: drwxrwx--- system   cache             2020-09-04 15:20 cache
        # files: -rwxr-x--- root     root       526472 1970-01-01 02:00 init

        try:
            check_for_missing_dir = files_list[0]
        except IndexError:
            return []

        if 'No such file or directory' in check_for_missing_dir \
                or "Not a directory" in check_for_missing_dir:
            return None

        ret_list = list()

        for item in files_list:
            item_split = list()

            for listed_item in item.split(" "):
                if listed_item != '':
                    item_split.append(listed_item)

            item_flags = item_split[0]

            if 'd' in item_flags:
                # It's a dir
                file_type = 'dir'
            elif 'l' in item_flags:
                # It's a link
                file_type = 'link'
            else:
                # It's a file
                file_type = 'file'

            item_owner = item_split[1]
            item_owner_group = item_split[2]

            if file_type != 'link':
                item_date = item_split[-3]
                item_time = item_split[-2]
                item_name = item_split[-1]
                if file_type == 'file':
                    try:
                        item_size = int(item_split[-4])
                    except ValueError:
                        item_size = None
            else:
                item_date = item_split[3]
                item_time = item_split[4]
                item_name = item_split[5]
                item_link_endpoint = item_split[7]

            ret_list.append(
                {
                    'file_type': file_type,
                    'owner': item_owner,
                    'owner_group': item_owner_group,
                    'date': item_date,
                    'time': item_time,
                    'name': item_name
                }
            )

            # print(f"{file_type} '{item_name}' owned by {item_owner}:{item_owner_group} from {item_date} {item_time} \t {item_flags}")
            if file_type == 'file':
                ret_list[-1]['file_size'] = item_size
            elif file_type == 'link':
                ret_list[-1]['link_endpoint'] = item_link_endpoint

        ret_list.sort(key=lambda x: x['file_type'])
        logger.debug(f"Returning list: {ret_list}")

        return ret_list

    def get_files_list(self, target_dir, get_full_path=False):
        """
        Get a list of files in sdcard/DCIM/Camera on the device
        :return: List of strings, each being a file located in sdcard/DCIM/Camera
        """

        files_list = self.exec_shell(f"ls {'-d' if get_full_path else ''} {target_dir.rstrip('/')}/*").splitlines()
        logger.debug(f"Files List: {files_list}")
        try:
            check_for_missing_dir = files_list[0]
        except IndexError:
            return []

        if 'No such file or directory' in check_for_missing_dir \
                or "Not a directory" in check_for_missing_dir:
            return None
        else:
            return files_list

    def get_camera_files_list(self):
        self.get_files_list("sdcard/DCIM/Camera", get_full_path=True)

    def get_screen_resolution(self):
        """
        Get screen resolution of device
        :return:List height and width
        """
        try:
            res = self.exec_shell('dumpsys window | grep "mUnrestricted"').strip().split(' ')[1].split('x')
        except IndexError:
            res = self.exec_shell('dumpsys window | grep "mUnrestricted"').rstrip().split('][')[1].strip(']').split(',')

        return res

    def get_wakefulness(self):
        try:
            return self.exec_shell("dumpsys activity | grep -E 'mWakefulness'").split('=')[1]
        except IndexError:
            logger.warn('There was an issue with getting device wakefullness - probably a shell error!')
            return None

    def get_device_leds(self):
        """
        Get a list of the leds that the device has
        :return:None
        """
        return natsorted(self.exec_shell("ls /sys/class/leds/").strip().replace('\n', '').replace('  ', ' ').split(' '))

    # ----- Binary getters -----

    def has_screen(self):  # TODO Make this return a valid boolean (now it sometimes works, sometimes doesn't)
        """
        Check if the device has an integrated screen (not working all the time)
        :return:Bool Should return a Bool
        """
        before = self.exec_shell("dumpsys deviceidle | grep mScreenOn").split('=')[1].strip()
        self.exec_shell('input keyevent 26')
        sleep(0.5)
        after = self.exec_shell("dumpsys deviceidle | grep mScreenOn").split('=')[1].strip()

        if before == after:
            logger.info("Device has no integrated screen!")

        self.exec_shell('input keyevent 26')

    def is_sleeping(self):
        response = self.exec_shell("dumpsys activity | grep -E 'mSleeping'")
        state = response.strip() if response else None

        if response is None:
            return

        if "No such file" in state:
            logger.error(f"Found no such file in state: {state}")
            return None, None

        try:
            state = state.split(' ')
            is_sleeping = state[0].split('=')[1]
        except IndexError as e:
            is_sleeping = None
            logger.error(f"State: {state}\n{e}")

        try:
            lock_screen = state[1].split('=')[1]
        except IndexError as e:
            lock_screen = None
            logger.error(f"State: {state}\n{e}")
        return is_sleeping, lock_screen

    def is_adb_enabled(self):
        # Kind of useless as if this is actually false, we will not be able to connect
        return True if self.exec_shell('settings get global adb_enabled').strip() == '1' else False

    # ----- Device Actions -----
    def reboot(self):
        """
        Reboots the device.
        :return:None
        """
        self.exec_shell("reboot")  # TODO Remove device from connected_devices list after reboot
        # self.adb.detach_device(self.device_serial, self)

    def input_tap(self, *coords):  # Send tap events
        """
        Sends tap input to device
        :param coords: tap coordinates to use
        :return:None
        """
        logger.debug(f"X: {coords[0][0]}, Y: {coords[0][1]}")

        if self.android_ver <= 5:
            return self.exec_shell("input touchscreen tap {} {}".format(coords[0][0], coords[0][1]))
        else:
            return self.exec_shell("input tap {} {}".format(coords[0][0], coords[0][1]))

    def open_app(self, package):
        """
        Open an app package
        :param package: Specify the app package that you want to open
        :return:None
        """
        if self.get_current_app()[0] != package:
            logger.debug(f'Currently opened: {self.get_current_app()}')
            logger.debug("Opening {}...".format(package))
            self.exec_shell("monkey -p '{}' -v 1".format(package))
            sleep(1)  # Give a bit of time to the device to load the app
        else:
            logger.debug("{} was already opened! Continuing...".format(package))

    def clear_folder(self, folder):
        """
        Deletes a folder's contents
        :return:None
        """
        self.exec_shell(f"rm -rf {folder}/*")
        logger.debug(f"Deleting folder {folder} from device!")

    def pull_and_rename(self, dest, filename):
        pulled_files = []
        suffix = None
        files_list = self.get_camera_files_list()
        if not files_list:
            return []
        for num, file in enumerate(files_list):
            if num > 0:
                suffix = f"_{str(num)}"
            new_filename = path.join(dest, f"{filename}{suffix if suffix else ''}.{file.split('.')[1]}")
            self.pull_file(f"sdcard/DCIM/Camera/{file}", new_filename)
            pulled_files.append(new_filename)
        return pulled_files

    def setup_device_settings(self):
        # TODO: Make this save initial settings and set them back on exit
        logger.info('Making the device an insomniac!')
        self.exec_shell('settings put global stay_on_while_plugged_in 1')
        self.exec_shell('settings put system screen_off_timeout 9999999')

    def push_files(self, files_list, files_dest):
        logger.debug(f'Files list: {files_list}')

        for file in files_list.split(';'):
            logger.debug(f'Pushing: {file}')
            filename = path.basename(file)
            self.push_file(path.normpath(file), files_dest + filename)

    def turn_on_and_unlock(self):
        state = self.is_sleeping()
        if state is None:
            return

        if state[0] == 'true':
            self.exec_shell('input keyevent 26')  # Event Power Button
            self.exec_shell('input keyevent 82')  # Unlock

    def set_led_color(self, value, led, target):
        """
        Send a value to a led and a target
        ex: /sys/class/leds/RGB1/group_onoff - led is RGB1, target is group_onoff
        :param value: RGB HEX Value to send
        :param led: To which led to send
        :param target: To which target to send
        :return:None
        """
        try:
            self.exec_shell('echo {} > /sys/class/leds/{}/{}'.format(value, led, target))
            self.exec_shell('echo 60 > /sys/class/leds/{}/global_enable'.format(led))  # Poly
        except RuntimeError:
            logger.warn("Device was disconnected before we could detach it properly.. :(")

    def open_device_ctrl(self, extra_args=None):
        """
        Open device screen view and control using scrcpy
        :return:None
        """
        exec_data = [constants.SCRCPY, '--serial', self.device_serial]

        logger.info(f"Opening scrcpy for device {self.device_serial}.")

        logger.debug(f"Scrcpy extra_args: {extra_args}")
        if extra_args:
            extra_args = extra_args.split(" ")
            exec_data.append(extra_args)

        self.scrcpy.append(Popen(exec_data,
                                 stdin=PIPE,
                                 stdout=PIPE,
                                 stderr=PIPE,
                                 creationflags=constants.CREATE_NO_WINDOW))
        # self.scrcpy[-1].stdin.close()

    def record_device_ctrl(self, save_dest):
        self.kill_scrcpy()

        filename = f"{self.friendly_name}_screenrec_{datetime.now().strftime('%Y%m%d-%H%M%S')}.mp4"
        save_dest = path.join(save_dest, filename)

        logger.info(f"Starting device screen recording to: {save_dest}")

        self.open_device_ctrl(f"-r {save_dest}")

    def identify(self):
        """
        Identify device by blinking it's screen or leds
        :return:None
        """
        leds = self.get_device_leds()
        logger.debug(f"Device leds: {leds}")  # Debugging

        # Poly
        self.exec_shell('echo 1 > /sys/class/leds/{}/global_onoff'.format(leds[0]))

        for k in range(1, 60, 5):  # Blink Leds and screen
            # Poly
            if k != 1:
                sleep(0.3)
            self.exec_shell('echo {}{}{} > /sys/class/leds/{}/global_enable'.format(k, k, k, leds[0]))  # Poly

            # Devices with screen
            if (k % 11) % 2:
                self.exec_shell('input keyevent 26')  # Event Power Button

        self.exec_shell('echo 60 > /sys/class/leds/{}/global_enable'.format(leds[0]))  # Poly
        logger.info('Finished identifying!')

    def kill_scrcpy(self):
        logger.debug(f"Scrcpy list: {self.scrcpy}")
        scrcpy_list = self.scrcpy.copy()

        for process in scrcpy_list:
            try:
                stdout_data = process.communicate(input=b'\x03')[0]  # Send Ctrl+C
                logger.debug(stdout_data)
            except ValueError:
                logger.warn("Window was already closed!")

            logger.debug(f"killing {process.pid}")
            process.terminate()

            self.scrcpy.remove(process)

        logger.debug("Killed scrcpy windows for device")
        del scrcpy_list

    # ----- Settings Persistence -----
    def load_settings_file(self):
        root = super().load_settings_file()
        if root is None:
            return

        # all item attributes
        for elem in root:
            for subelem in elem:
                if subelem.tag == 'serial' and subelem.text != self.device_serial:
                    logger.error('XML ERROR! Serial mismatch!')

                if subelem.tag == 'friendly_name':
                    self.friendly_name = subelem.text

                if subelem.tag == 'camera_app':
                    self.camera_app = subelem.text

                if subelem.tag == 'logs':
                    for data in subelem:
                        if data.tag == 'enabled':
                            if data.text == '1':
                                self.logs_enabled = True
                            else:
                                self.logs_enabled = False
                        if data.tag == 'filter':
                            self.logs_filter = data.text if data.text is not None else ''

                for seq_type in list(constants.ACT_SEQUENCES.keys()):
                    if subelem.tag == constants.ACT_SEQUENCES[seq_type]:
                        setattr(self, constants.ACT_SEQUENCES[seq_type], generate_sequence(subelem))
                        logger.debug(f'Device Obj Seq List: {getattr(self, constants.ACT_SEQUENCES[seq_type])}')

                if subelem.tag == 'actions_time_gap':
                    self.actions_time_gap = int(subelem.text)

    def save_settings(self):
        root = ET.Element('device')

        # Device info
        info = ET.SubElement(root, 'info')

        serial = ET.SubElement(info, "serial")
        serial.text = self.device_serial

        manufacturer = ET.SubElement(info, "manufacturer")
        manufacturer.text = self.get_manufacturer()

        board = ET.SubElement(info, "board")
        board.text = self.get_board()

        name = ET.SubElement(info, "name")
        name.text = self.get_device_name()

        model = ET.SubElement(info, "model")
        model.text = self.get_device_model()

        cpu = ET.SubElement(info, "cpu")
        cpu.text = self.get_cpu()

        resolution = ET.SubElement(info, "screen_resolution")
        res_data = self.get_screen_resolution()
        resolution.text = f'{res_data[0]}x{res_data[1]}'

        android_version = ET.SubElement(info, "android_version")
        android_version.text = self.get_android_version()

        friendly = ET.SubElement(info, "friendly_name")
        friendly.text = self.friendly_name

        # Device settings
        settings = ET.SubElement(root, 'settings')

        cam_app = ET.SubElement(settings, "camera_app")
        cam_app.text = self.camera_app

        logs = ET.SubElement(settings, "logs")

        logs_bool = ET.SubElement(logs, "enabled")
        logs_bool.text = str(1 if self.logs_enabled else 0)

        logs_filter = ET.SubElement(logs, "filter")
        logs_filter.text = self.logs_filter

        for seq_type in list(constants.ACT_SEQUENCES.keys()):
            curr_seq = ET.SubElement(settings, constants.ACT_SEQUENCES[seq_type])
            xml_from_sequence(self, constants.ACT_SEQUENCES[seq_type], curr_seq)

        actions_time_gap = ET.SubElement(settings, "actions_time_gap")
        actions_time_gap.text = str(self.actions_time_gap)

        tree = ET.ElementTree(root)
        logger.info(f'Writing settings to file {self.device_xml}')
        tree.write(self.device_xml, encoding='UTF8', xml_declaration=True)

    # ----- Device UI Parsing -----
    def dump_window_elements(self):
        """
        Dump elements of currently opened app activity window
        and pull them from device to folder XML
        :return:None
        """
        source = self.exec_shell('uiautomator dump').split(': ')[1].rstrip()
        current_app = self.get_current_app()
        if source == "null root node returned by UiTestAutomationBridge.":
            logger.error("UIAutomator error! :( Try dumping UI elements again. (It looks like a known error)")
            return

        logger.debug(f'Source returned: {source}')

        self.pull_file(
            source,
            path.join(constants.XML_DIR,
                      '{}_{}_{}.xml'.format(self.device_serial, current_app[0], current_app[1]))
        )
        logger.info('Dumped window elements for current app.')

    def get_clickable_window_elements(self, force_dump=False):
        """
        Parse the dumped window elements file and filter only elements that are "clickable"
        :return:Dict key: element_id or number,
                value: String of elem description, touch location (a list of x and y)
        """
        logger.debug('Parsing UI XML...')
        current_app = self.get_current_app()

        if current_app is None:
            logger.error("Current app unknown... We don't know how to name the xml file so we will say NO! :D ")
            return {}

        logger.debug("Serial {} , app: {}".format(self.device_serial, current_app))
        file = path.join(constants.XML_DIR,
                         '{}_{}_{}.xml'.format(self.device_serial, current_app[0], current_app[1]))

        if force_dump:
            self.dump_window_elements()

        xml_tree = None

        try:
            xml_tree = ET.parse(file)
        except FileNotFoundError:
            logger.info('XML for this UI not found, dumping a new one...')
            self.dump_window_elements()
            xml_tree = ET.parse(file)
        except ET.ParseError as error:
            logger.error(f"XML Parse Error: {error}")

        try:
            xml_root = xml_tree.getroot()
        except AttributeError:
            logger.error("XML wasn't opened correctly!")
            return
        except UnboundLocalError:
            logger.warn("UI Elements XML is probably empty... :( Retrying...")
            self.dump_window_elements()
            xml_tree = ET.parse(file)
            xml_root = xml_tree.getroot()
        elements = {}

        for num, element in enumerate(xml_root.iter("node")):
            elem_res_id = element.attrib['resource-id'].split('/')
            elem_desc = element.attrib['content-desc']
            elem_bounds = findall(r'\[([^]]*)]', element.attrib['bounds'])[0].split(',')

            if (elem_res_id or elem_desc) and int(elem_bounds[0]) > 0:
                elem_bounds[0] = int(elem_bounds[0]) + 1
                elem_bounds[1] = int(elem_bounds[1]) + 1
                if elem_res_id[0] != '':
                    try:
                        elements[elem_res_id[1]] = elem_desc, elem_bounds
                    except IndexError:
                        # For elements that don't have an app id as first element
                        elements[elem_res_id[0]] = elem_desc, elem_bounds
                else:
                    elements[num] = elem_desc, elem_bounds

        return elements

    # ----- Actions Parsing -----
    def do(self, sequence):
        """
        Parses an actions sequence that is passed
        :param sequence: List of actions
        :return:
        """
        self.open_app(self.camera_app)

        logger.debug(f'Doing sequence using device {self.device_serial}')

        for action in sequence:
            act_id = action[0]
            act_data = action[1]
            act_type = act_data[2]
            act_value = act_data[1]
            logger.debug(f"Performing {act_id}")
            if act_type == 'tap':
                self.input_tap(act_value)
            if act_type == 'delay':
                logger.debug(f"Sleeping {act_value}")
                sleep(int(act_value))
            sleep(self.actions_time_gap)

    def take_photo(self):
        logger.debug(f"Current mode: {self.current_camera_app_mode}")
        if self.current_camera_app_mode != 'photo':
            self.do(self.goto_photo_seq)
            self.current_camera_app_mode = 'photo'
        self.do(self.shoot_photo_seq)

    def start_video(self):
        logger.debug(f"Current mode: {self.current_camera_app_mode}")
        if self.current_camera_app_mode != 'video':
            self.do(self.goto_video_seq)
            self.current_camera_app_mode = 'video'
            self.is_recording_video = True
        self.do(self.start_video_seq)

    def stop_video(self):
        if self.is_recording_video:
            self.do(self.stop_video_seq)

    # ----- Other -----
    def print_attributes(self):
        # For debugging
        logger.debug("Object properties:\n")
        logger.debug(f"Friendly Name: {self.friendly_name}")
        logger.debug(f"Serial: {self.device_serial}")
        logger.debug(f"Cam app: {self.camera_app}")
        logger.debug(f"Logs: enabled ({self.logs_enabled}), filter ({self.logs_filter})")
        logger.debug(f"shoot_photo_seq: {self.shoot_photo_seq}")
        logger.debug(f"start_video_seq: {self.start_video_seq}")
        logger.debug(f"stop_video_seq: {self.stop_video_seq}")
        logger.debug(f"goto_photo_seq: {self.goto_photo_seq}")
        logger.debug(f"goto_video_seq: {self.goto_video_seq}")
        logger.debug(f"actions_time_gap: {self.actions_time_gap}")
        logger.debug(f"settings xml file location: {self.device_xml}")
