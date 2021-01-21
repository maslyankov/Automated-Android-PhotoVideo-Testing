import json
import os
import threading

# Local
from src import constants
from src.logs import logger

# Imatest
try:
    from imatest.it import ImatestLibrary, ImatestException
except RuntimeError:
    logger.error('Imatest Import error (Check MathLAB path)!')
except ModuleNotFoundError:
    logger.warn('Imatest IT Python Library not found!')
    SKIP_IMATEST_IT = True


class ImatestAnalysis:
    def __init__(self):
        if SKIP_IMATEST_IT:
            return

        try:
            self.imatest = ImatestLibrary()
        except ImatestException.MatlabException as e:
            logger.exception('Imatest: MathLab Error!')
            raise RuntimeWarning('Imatest: MathLab Error!\n', e)
        except ImatestException.LicenseException as e:
            logger.exception('Imatest: License Error!')
            raise RuntimeWarning('Imatest: License Error!\n', e)
        except RuntimeError as e:
            logger.exception('Imatest: Runtime Error!\n')

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

        logger.debug(f'Input list: {input_files}')

        # Only other modules are "Arbitrary Charts" and "OIS" - they want different arguments
        test_type_call = self.imatest_analysis_type(test_type, parallel=False)

        # Call to esfriso using Op Mode Standard, with ini file argument and JSON output
        # with multiple files.
        # input_file argument is a list containing the full paths to several images.
        # Output is a JSON string containing the result of the last image

        try:
            result = test_type_call(input_file=input_files,
                                    root_dir=root_dir,
                                    op_mode=op_mode,
                                    ini_file=ini_file)

            logger.debug(f"Result: {result}")
        except ImatestException as iex:
            if iex.error_id == ImatestException.FloatingLicenseException:
                logger.error("All floating license seats are in use. Exit Imatest on another computer and try again.")
            elif iex.error_id == ImatestException.LicenseException:
                logger.error("License Exception: " + iex.message)
            else:
                logger.error(iex.message)
        except Exception as e:
            logger.exception(str(e))

        return json.loads(result)  # Return readable json object

    def analyze_images_parallel(self, images, ini_file, num_processes: int = 4):
        tasks = []

        for device_serial in images.keys():
            for test_num, test_dict in enumerate(images[device_serial]):
                logger.info(f"ADDING TASK - {test_dict['analysis_type']}\n{test_dict['image_files']}")
                tasks.append(
                    self.imatest.new_parallel_task(
                        image_files=test_dict['image_files'],
                        analysis_type=self.imatest_analysis_type(test_dict['analysis_type'])
                    )
                )

        result = self.imatest.parallel_analyzer(tasks=tasks, ini_file=ini_file, run_parallel=True,
                                                num_workers=num_processes)

        return json.loads(result)  # Return readable json object

    def imatest_analysis_type(self, test_type, parallel=True):
        # Filter out special characters and spaces
        test_type = ''.join(filter(str.isalnum, test_type.lower()))

        if parallel:
            test_types_dict = constants.IMATEST_PARALLEL_TEST_TYPES
        else:
            test_types_dict = constants.IMATEST_TEST_TYPES

        for tt in test_types_dict.keys():
            if test_type == tt:
                logger.debug(f'For analysis type {test_type} we found {getattr(self.imatest, test_types_dict[tt])}')  # DEBUG
                return getattr(self.imatest, test_types_dict[tt])
        # if it still hasn't returned, then will come through here
        logger.error('Analysis Type not found in IMATEST_TEST_TYPES: ', test_type)

    def __del__(self):
        logger.info("Terminating Imatest Library")
        # When finished terminate the library
        self.imatest.terminate_library()

    # Static Methods
    @staticmethod
    def recurse_dict(d, keys=()):
        if type(d) == dict:
            for k in d:
                for rv in ImatestAnalysis.recurse_dict(d[k], keys + (k,)):
                    yield rv
        else:
            yield keys, d

    @staticmethod
    def update_imatest_params(json_file=None, test_type=None):
        if test_type is not None:
            if json_file is None:
                return
            elif not json_file.endswith('.json'):
                return

        params_out_file = os.path.join(constants.DATA_DIR, 'imatest_params.json')

        if json_file is None:
            report_obj = ImatestAnalysis()
            images_dict = {'test_serial': []}
            tests_params = {}
            curr_progress = 0
            ini_file = os.path.join(constants.ROOT_DIR, 'images', 'imatest', 'ini_file', 'imatest-v2.ini')

            prog_step = 100 / len(constants.IMATEST_PARALLEL_TEST_TYPES.keys()) / 3

            # Prepare list for passing to image analyzer
            tests_list = images_dict['test_serial']
            for test_name in constants.IMATEST_PARALLEL_TEST_TYPES.keys():
                img_file = os.path.join(constants.ROOT_DIR, 'images', 'imatest', f'{test_name}_example')
                if os.path.exists(img_file + '.jpg'):
                    img_file += '.jpg'
                elif os.path.exists(img_file + '.png'):
                    img_file += '.png'
                else:
                    logger.error(f'FAILED TO FIND IMAGE FOR {img_file}')
                    continue

                new_dict = {
                    'analysis_type': test_name,
                    'image_files': [img_file]
                }

                tests_list.append(new_dict)

            logger.debug(f'Created images dict:\n {images_dict}')
            result = report_obj.analyze_images_parallel(images_dict, ini_file)
            # open output file for writing
            result_out_file = os.path.join(constants.DATA_DIR, 'imatest_all_tests_results.json')
            with open(result_out_file, 'w') as outfile:
                json.dump(result, outfile)

            logger.debug(f'Analysis Result:\n{result}')
        else:
            if test_type is None:
                logger.error('UPD_IMATEST_PARAMS: JSON_FILE not None, but test_type is None.')
                return

            # Load current params file
            with open(params_out_file) as params_file_old:
                last_params_readable = json.load(params_file_old)
            tests_params = last_params_readable

            logger.debug(f'tests_params: \n{tests_params}')

            with open(json_file) as json_file_l:
                image_analysis_readable = json.load(json_file_l)
            result = [image_analysis_readable]

            logger.debug(f'result: \n{result}')

        # Parse received list to params file
        filter_params = [
            'dateRun', 'ini_time_size', 'version', 'buildDate', 'title',
            'image_file', 'image_path_name', 'build', 'EXIF_results',
            'errorID', 'errorMessage', 'errorReport',
            '_ArrayType_', '_ArraySize_', '_ArrayData_'
        ]

        # for res_dict in images_analysis_readable:
        for res_dict in result:
            current_type = None
            for key, value in ImatestAnalysis.recurse_dict(res_dict[list(res_dict.keys())[0]]):
                if current_type is None or key[0] == 'title' or key[0] == 'image_file':
                    # First find the title
                    # Turns out dotpattern has neither title, nor image_file keys..
                    # if key[0] == 'title' or key[0] == 'image_file':
                    #     current_type = value.split('_')[0]
                    if test_type is not None:
                        if key[0] == 'title' or key[0] == 'image_file':
                            continue
                        current_type = test_type
                        del tests_params[current_type]
                    elif key[0] == 'version':
                        current_type = value.split('  ')[-1].split('_')[0].replace(' ', '').lower()
                    elif key[0] == 'title' or key[0] == 'image_file':
                        last_type_name = None
                        if current_type in list(tests_params.keys()):
                            last_type_name = current_type
                        current_type = value.split('_')[0]

                        if last_type_name:
                            tests_params[current_type] = tests_params[last_type_name]
                            del tests_params[last_type_name]
                            print(f'moved and deleted params from {last_type_name} to {current_type}')
                else:
                    param_name = '>'.join(key)
                    val_type = type(value).__name__
                    if val_type == type(str).__name__ or key[-1] in filter_params:
                        # Skip string or filtered params
                        logger.info(f'Skipping {key[-1]} because it is a string or in filter!')
                        continue
                    if val_type == 'list' and len(value) == 1:
                        val_type = type(value[0]).__name__
                    try:
                        tests_params[current_type]
                    except KeyError:
                        tests_params[current_type] = {}
                        tests_params[current_type][param_name] = val_type
                    else:
                        tests_params[current_type][param_name] = val_type

        # open output file for writing
        with open(params_out_file, 'w') as outfile:
            json.dump(tests_params, outfile)

    @staticmethod
    def update_imatest_params_threaded():
        threading.Thread(target=ImatestAnalysis.update_imatest_params,
                         args=(),
                         daemon=True).start()
