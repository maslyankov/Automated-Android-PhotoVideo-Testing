import os

from openpyxl import Workbook, load_workbook
from openpyxl import cell as xlcell, worksheet
import win32com.client as win32

try:
    from imatest.it import ImatestLibrary, ImatestException
except RuntimeError as e:
    print('Fatal Reports Error: ', e)

import src.constants as constants
from src.app.utils import kelvin_to_illumenant, only_digits, only_chars


class Report:
    def __init__(self):
        self.imatest = ImatestLibrary()

    def analyze_images(self, test_type, root_dir, images_list):
        result = None

        # root_dir = os.path.normpath(r'C:\Program Files\Imatest\v2020.2\IT\samples\python\esfriso')

        # root_dir = os.path.normpath(r'C:\Users\mms00519\Desktop\test_batch')
        # images_dir = os.path.join(root_dir, 'Images')
        # # input_file = os.path.join(images_dir, r'ESFR_50.jpg')
        # images = ['ESFR_50.jpg', 'ESFR_50.jpg']

        ini_file = os.path.join(root_dir, r'settings-p30.ini')
        op_mode = ImatestLibrary.OP_MODE_SEPARATE

        input_files = []

        for image in images_list:
            input_files.append(image)

        print('Input list: ', input_files)

        test_type_call = None
        if test_type == 'sfr':
            test_type_call = self.imatest.sfr_json
        elif test_type == 'sfrplus':
            test_type_call = self.imatest.sfrplus_json
        elif test_type == 'star':
            test_type_call = self.imatest.star_json
        elif test_type == 'colorcheck':
            test_type_call = self.imatest.colorcheck_json
        elif test_type == 'stepchart':
            test_type_call = self.imatest.stepchart_json
        elif test_type == 'wedge':
            test_type_call = self.imatest.wedge_json
        elif test_type == 'uniformity':
            test_type_call = self.imatest.uniformity_json
        elif test_type == 'distortion':
            test_type_call = self.imatest.distortion_json
        elif test_type == 'esfriso':
            test_type_call = self.imatest.esfriso_json
        elif test_type == 'blemish':
            test_type_call = self.imatest.blemish_json
        elif test_type == 'dotpattern':
            test_type_call = self.imatest.dotpattern_json
        elif test_type == 'color_tone':
            test_type_call = self.imatest.color_tone_json
        elif test_type == 'checkerboard':
            test_type_call = self.imatest.checkerboard_json
        elif test_type == 'random':
            test_type_call = self.imatest.random_json
        elif test_type == 'sfrreg':
            test_type_call = self.imatest.sfrreg_json
        elif test_type == 'logfc':
            test_type_call = self.imatest.logfc_json
        # Only other modules are "Arbitrary Charts" and "OIS" - they want different arguments

        # Call to esfriso using Op Mode Standard, with ini file argument and JSON output
        # with multiple files.
        # input_file argument is a list containing the full paths to several images.
        # Output is a JSON string containing the result of the last image

        try:
            result = test_type_call(input_file=input_files,
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

        return result

    def analyze_images_parallel(self, images, ini_file, num_processes: int = 4):
        tasks = []

        tasks.append(self.imatest.new_parallel_task(image_files=r'C:\images\sfrplus_0123.jpg',
                                                    analysis_type=self.imatest.SFRPLUS_ANALYSIS))
        tasks.append(self.imatest.new_parallel_task(
            image_files=[r'C:\images\blemish_0001.jpg', r'C:\images\blemish_0002.jpg', r'C:\images\blemish_0003.jpg'],
            analysis_type=self.imatest.BLEMISH_ANALYSIS))

        result = self.imatest.parallel_analyzer(tasks=tasks, ini_file=ini_file, run_parallel=True,
                                                num_workers=num_processes)

        print(result)

    def __del__(self):
        print("Terminating Imatest Library")
        # When finished terminate the library
        self.imatest.terminate_library()

    # Static Methods
    @staticmethod
    def xls_to_xlsx(xls_file) -> str:
        excel = win32.gencache.EnsureDispatch('Excel.Application')
        wb = excel.Workbooks.Open(xls_file)
        new_file = xls_file + "x"

        wb.SaveAs(new_file, FileFormat=51)  # FileFormat = 51 is for .xlsx extension
        wb.Close()  # FileFormat = 56 is for .xls extension
        excel.Application.Quit()

        return new_file

    @staticmethod
    def within_range(bounds: tuple, cell: xlcell) -> bool:
        column_start, row_start, column_end, row_end = bounds
        row = cell.row
        if row_start <= row <= row_end:
            column = cell.column
            if column_start <= column <= column_end:
                return True
        return False

    @staticmethod
    def get_value_merged(sheet: worksheet, cell: xlcell) -> any:
        for merged in sheet.merged_cells:
            if Report.within_range(merged.bounds, cell):
                return sheet.cell(merged.min_row, merged.min_col).value
        return cell.value

    @staticmethod
    def is_merged(cell) -> bool:
        if type(cell).__name__ == 'MergedCell':
            return True
        else:
            return False

    @staticmethod
    def get_cell_val(ws, cell):
        return Report.get_value_merged(ws, cell) if Report.is_merged(cell) else cell.value

    @staticmethod
    def parse_excel_template(excel_file) -> dict:
        # Config
        header_mapping = {
            'test_type': "test target",
            'light_temp': "light",
            'lux': "lux",
            'param': "param",
            'min': "min",
            'max': "max"
        }
        conf_min_col = 1
        conf_min_row = 4
        conf_max_row = 77
        filter_str = 'functional'
        # Config end

        excel_file = os.path.normpath(excel_file)
        print(f'Parsing "{excel_file}"...')

        ext = excel_file.split('.')[-1]

        if ext == 'xls':
            print("Got .XLS.. Converting it to XLSX")
            excel_file = Report.xls_to_xlsx(excel_file)

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
            if header_mapping['test_type'] in cell.value.lower():
                test_type_col = cell.column_letter

            if header_mapping['light_temp'] in cell.value.lower():
                light_temp_col = cell.column_letter

            if header_mapping['lux'] in cell.value.lower():
                lux_col = cell.column_letter

            if header_mapping['param'] in cell.value.lower():
                param_col = cell.column_letter

            if header_mapping['min'] in cell.value.lower():
                min_col = cell.column_letter

            if header_mapping['max'] in cell.value.lower():
                max_col = cell.column_letter

        print(
            f"Test Type: {test_type_col}, \nLight Temp: {light_temp_col}, \nLux: {lux_col}, \nParams: {param_col}, \nMin: {min_col}, \nMax: {max_col}\n")

        current_tt = None
        current_temp = None
        current_lux = None
        current_param = None

        for row in ws.iter_rows(min_col=conf_min_col, min_row=conf_min_row, max_row=conf_max_row):
            for cell in row:
                value = Report.get_cell_val(ws, cell)
                # print(value, only_chars(cell.coordinate))  # Debugging
                # print(f'curr temp: {current_temp}, curr lux: {current_lux}, current param: {current_param}')  # Debugging
                if value is not None and isinstance(value, str) and filter_str in value.lower():
                    break

                col = only_chars(cell.coordinate)
                if col == test_type_col:  # Test type
                    if value is not None:
                        current_tt = value.strip().replace('\n', '')
                        try:
                            tests_seq[current_tt]
                        except KeyError:
                            tests_seq[current_tt] = {}
                        print('\n\nType: ' + current_tt)
                    else:
                        current_tt = None

                if col == light_temp_col:  # Light Temperature
                    if value is not None and current_tt is not None:
                        current_temp = kelvin_to_illumenant(value)
                        try:
                            tests_seq[current_tt][current_temp]
                        except KeyError:
                            tests_seq[current_tt][current_temp] = {}
                        print('Light Temp: ' + current_temp)
                    else:
                        current_temp = None

                if col == lux_col:  # LUX
                    if value is not None and current_temp is not None:
                        current_lux = only_digits(value)
                        try:
                            tests_seq[current_tt][current_temp][current_lux]
                        except KeyError:
                            tests_seq[current_tt][current_temp][current_lux] = {}
                        print('- LUX: ' + str(current_lux))
                    else:
                        current_lux = None

                if col == param_col:  # Params
                    if value is not None and current_lux is not None:
                        current_param = value
                        tests_seq[current_tt][current_temp][current_lux][current_param] = {}
                        print('\tPARAM: ' + str(current_param))
                    else:
                        current_param = None

                if col == min_col:  # Min
                    if current_param is not None:
                        if current_param not in tests_seq[current_tt][current_temp][current_lux]:
                            tests_seq[current_tt][current_temp][current_lux][current_param] = {}

                        tests_seq[current_tt][current_temp][current_lux][current_param]['min'] = value

                        print('\tMin: ' + str(value))

                if col == max_col:  # Max
                    if current_param is not None:
                        tests_seq[current_tt][current_temp][current_lux][current_param]['max'] = value
                        print('\tMax: ' + str(value) + '\n')

        return tests_seq

    @staticmethod
    def generate_lights_seqs(req_dict):
        lights_list = []

        for test_type in req_dict.keys():
            lights_list.append(
                {
                    'test_type': test_type,
                    'lights_seq': {}
                }
            )
            for light_type in req_dict[test_type].keys():
                lights_list[len(lights_list) - 1]['lights_seq'][light_type] = []
                for lux in req_dict[test_type][light_type].keys():
                    lights_list[len(lights_list) - 1]['lights_seq'][light_type].append(lux)

        return lights_list
