import os

from imatest.it import ImatestLibrary, ImatestException

from openpyxl import Workbook, load_workbook
from openpyxl import cell as xlcell, worksheet
import win32com.client as win32

from src.app.utils import kelvin_to_illumenant, only_digits

def xls_to_xlsx(xls_file):
    excel = win32.gencache.EnsureDispatch('Excel.Application')
    wb = excel.Workbooks.Open(xls_file)
    new_file = xls_file + "x"

    wb.SaveAs(new_file, FileFormat=51)  # FileFormat = 51 is for .xlsx extension
    wb.Close()  # FileFormat = 56 is for .xls extension
    excel.Application.Quit()

    return new_file


def within_range(bounds: tuple, cell: xlcell) -> bool:
    column_start, row_start, column_end, row_end = bounds
    row = cell.row
    if row_start <= row <= row_end:
        column = cell.column
        if column_start <= column <= column_end:
            return True
    return False


def get_value_merged(sheet: worksheet, cell: xlcell) -> any:
    for merged in sheet.merged_cells:
        if within_range(merged.bounds, cell):
            return sheet.cell(merged.min_row, merged.min_col).value
    return cell.value


def is_merged(cell):
    if type(cell).__name__ == 'MergedCell':
        return True
    else:
        return False


def get_cell_val(ws, cell):
    return get_value_merged(ws, cell) if is_merged(cell) else cell.value


def parse_excel_template(excel_file):
    excel_file = os.path.normpath(excel_file)
    print(f'Parsing "{excel_file}"...')

    ext = excel_file.split('.')[-1]

    if ext == 'xls':
        print("Got .XLS.. Converting it to XLSX")
        excel_file = xls_to_xlsx(excel_file)

    wb = load_workbook(filename=excel_file)
    ws = wb.worksheets[0]

    tests_seq = {}

    header = list(ws.rows)[1]
    test_type_col = None
    light_temp_col = None
    lux_col = None
    param_col = None
    min_col = None
    max_col = None

    for cell in header:
        if "test target" in cell.value.lower():
            test_type_col = cell.column_letter

        if "light" in cell.value.lower():
            light_temp_col = cell.column_letter

        if "lux" in cell.value.lower():
            lux_col = cell.column_letter

        if "param" in cell.value.lower():
            param_col = cell.column_letter

        if "min" in cell.value.lower():
            min_col = cell.column_letter

        if "max" in cell.value.lower():
            max_col = cell.column_letter

    print(
        f"Test Type: {test_type_col}, \nLight Temp: {light_temp_col}, \nLux: {lux_col}, \nParams: {param_col}, \nMin: {min_col}, \nMax: {max_col}\n")

    # for row in ws.rows:
    #     for cell in row:
    #         print('is merged?: ' + str(is_merged(cell)))
    #         if is_merged(cell) and cell.value is not None:
    #             print('Cell Value: ' + str(cell.value))

    current_tt = None
    current_temp = None
    current_lux = None
    current_param = None

    for row in ws.iter_rows(min_col=1, min_row=4):
        for cell in row:
            value = get_cell_val(ws, cell)
            if hasattr(cell, "column_letter"):
                if cell.column_letter == test_type_col:  # Test type
                    if value is not None:
                        current_tt = value.strip()
                        tests_seq[current_tt] = {}
                        print('\n\nType: ' + current_tt)
                    else:
                        current_tt = None

                if cell.column_letter == light_temp_col:  # Light Temperature
                    if value is not None and current_tt is not None:
                        current_temp = kelvin_to_illumenant(value)
                        tests_seq[current_tt][current_temp] = {}
                        print('Light Temp: ' + current_temp)
                    else:
                        current_temp = None

                if cell.column_letter == lux_col:  # LUX
                    if value is not None and current_temp is not None:
                        current_lux = only_digits(value)
                        tests_seq[current_tt][current_temp][current_lux] = {}
                        print('- LUX: ' + str(current_lux))
                        #print(tests_seq)
                    else:
                        current_lux = None

                if cell.column_letter == param_col:  # Params
                    if value is not None and current_lux is not None:
                        current_param = value
                        tests_seq[current_tt][current_temp][current_lux][current_param] = {}
                        print('\tPARAM: ' + str(current_param))
                    else:
                        current_param = None

                if cell.column_letter == min_col:  # Min
                    if current_param is not None:
                        if current_param not in tests_seq[current_tt][current_temp][current_lux]:
                            tests_seq[current_tt][current_temp][current_lux][current_param] = {}

                        tests_seq[current_tt][current_temp][current_lux][current_param]['min'] = value

                        print('\tMin: ' + str(value))

                if cell.column_letter == max_col:  # Max
                    if current_param is not None:
                        tests_seq[current_tt][current_temp][current_lux][current_param]['max'] = value
                        print('\tMax: ' + str(value) + '\n')

    print(tests_seq)


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


parse_excel_template(r"C:\Users\mms00519\Downloads\Criteria-poly.xlsx")
