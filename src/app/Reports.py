import os
from imatest.it import ImatestLibrary, ImatestException
from openpyxl import Workbook, load_workbook
import win32com.client as win32


def xls_to_xlsx(xls_file):
    excel = win32.gencache.EnsureDispatch('Excel.Application')
    wb = excel.Workbooks.Open(xls_file)
    new_file = xls_file + "x"

    wb.SaveAs(new_file, FileFormat=51)  # FileFormat = 51 is for .xlsx extension
    wb.Close()  # FileFormat = 56 is for .xls extension
    excel.Application.Quit()

    return new_file


def parse_excel_template(excel_file):
    excel_file = os.path.normpath(excel_file)
    print(f'Parsing "{excel_file}"...')

    ext = excel_file.split('.')[-1]

    if ext == 'xls':
        print("Got .XLS.. Converting it to XLSX")
        excel_file = xls_to_xlsx(excel_file)

    wb = load_workbook(filename=excel_file)
    ws = wb.worksheets[0]

    header = ws['A2': 'J2']

    print('Tables', ws.tables)

    for cell in ws:
        cell


class Report:
    def __init__(self, report_type, images, ini_file, root_dir=None):
        self.report_type = report_type
        self.images = images
        self.root_dir = os.path.dirname(images[0]) if root_dir is not None else root_dir
        self.ini_file = ini_file
        print(root_dir)

    def analyze_images(self):
        imatest = ImatestLibrary()
        result = None

        # root_dir = os.path.normpath(r'C:\Program Files\Imatest\v2020.2\IT\samples\python\esfriso')

        # root_dir = os.path.normpath(r'C:\Users\mms00519\Desktop\test_batch')
        # images_dir = os.path.join(root_dir, 'Images')
        # # input_file = os.path.join(images_dir, r'ESFR_50.jpg')
        # images = ['ESFR_50.jpg', 'ESFR_50.jpg']

        ini_file = os.path.join(root_dir, r'settings-p30.ini')
        op_mode = ImatestLibrary.OP_MODE_SEPARATE

        input_files = []

        for image in self.images:
            input_files.append(image)

        print('Input list: ', input_files)

        try:
            result = imatest.esfriso(input_file=input_files,
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
