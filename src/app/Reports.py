import os
from imatest.it import ImatestLibrary, ImatestException


class Report:
    def __init__(self, report_type, image):
       self.type = type
       self.image = image

    @staticmethod
    def analyze_image():
        imatest = ImatestLibrary()
        result = None

        root_dir = os.path.normpath(r'C:\Program Files\Imatest\v2020.2\IT\samples\python\esfriso')
        images_dir = os.path.join(root_dir, os.pardir, os.pardir, 'images')
        input_file = os.path.join(images_dir, r'esfriso_example.jpg')

        op_mode = ImatestLibrary.OP_MODE_SEPARATE
        ini_file = os.path.join(root_dir, os.pardir, 'ini_file', r'imatest-v2.ini')

        try:
            result = imatest.esfriso(input_file=input_file,
                                     root_dir=root_dir,
                                     op_mode=op_mode,
                                     ini_file=ini_file)

            print(result)
        except ImatestException as iex:
            if iex.error_id == ImatestException.FloatingLicenseException:
                print("All floating license seats are in use.  Exit Imatest on another computer and try again.")
            elif iex.error_id == ImatestException.LicenseException:
                print("License Exception: " + iex.message)
            else:
                print(iex.message)
        except Exception as ex:
            print(str(ex))

        # Call to esfriso using Op Mode Standard, with ini file argument and JSON output
        # with multiple files.
        # input_file argument is a list containing the full paths to several images.
        # Output is a JSON string containing the result of the last image

        input_file = [os.path.join(images_dir, r'esfriso_example.jpg'),
                      os.path.join(images_dir, r'esfriso_example.jpg'),
                      os.path.join(images_dir, r'esfriso_example.jpg'),
                      os.path.join(images_dir, r'esfriso_example.jpg'),
                      os.path.join(images_dir, r'esfriso_example.jpg')]
        op_mode = ImatestLibrary.OP_MODE_SEPARATE
        ini_file = os.path.join(root_dir, os.pardir, 'ini_file', r'imatest-v2.ini')

        try:
            result = imatest.esfriso(input_file=input_file,
                                     root_dir=root_dir,
                                     op_mode=op_mode,
                                     ini_file=ini_file)

            print(result)
        except ImatestException as iex:
            if iex.error_id == ImatestException.FloatingLicenseException:
                print("All floating license seats are in use.  Exit Imatest on another computer and try again.")
            elif iex.error_id == ImatestException.LicenseException:
                print("License Exception: " + iex.message)
            else:
                print(iex.message)
        except Exception as ex:
            print(str(ex))

        # When finished terminate the library
        imatest.terminate_library()

        return result

Report.analyze_image()
