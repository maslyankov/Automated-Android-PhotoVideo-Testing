from __future__ import print_function
import os
import platform
import json
import array
import collections
import imatest.library
import matlab
import uuid
import re
from matlab._internal.mlarray_utils import _get_strides, _get_size, \
    _normalize_size, _get_mlsize, _reshape
from matlab_pysdk.runtime import MatlabRuntimeError

from matlab._internal.mlarray_sequence import flat, python_type
import imatest
from .ImatestException import _ImatestException


def mlarray__init__(self, typecode, initializer=None,
                    size=None, is_complex=False):
    """
    Provides a concrete implementation for the abstract
    base class collections.sequence.
    :param typecode: single character
    :param initializer: sequence
    :param size: sequence
    :param is_complex: bool
    """
    self._is_complex = is_complex
    self._python_type = python_type[typecode]
    if initializer is not None:
        if isinstance(initializer, array.array):
            arr_len = len(initializer)
            self._size = (1, arr_len)
            self._strides = [1, 1]
            self._data = initializer
        elif isinstance(initializer, matlab._internal.mlarray_sequence._MLArrayMetaClass):
            self._size = initializer._size
            self._strides = initializer._strides
            self._data = initializer._data
        else:
            init_dims = _get_size(initializer)
            try:
                self._size = _normalize_size(size, init_dims)
            except matlab.ShapeError as ex:
                raise ex
            except matlab.SizeError as ex:
                raise ex
            strides = _get_strides(self._size)
            self._strides = strides[:-1]
            try:
                if is_complex:
                    complex_array = flat(self, initializer,
                                         init_dims, typecode)
                    self._real = complex_array['real']
                    self._imag = complex_array['imag']
                else:
                    self._data = flat(self, initializer, init_dims, typecode)
            except:
                raise

    else:
        # initializer is None
        if size is not None:
            self._size = _get_mlsize(size)
            strides = _get_strides(self._size)
            self._strides = strides[:-1]
            if is_complex:
                self._real = array.array(typecode, [0]) * strides[-1]
                self._imag = array.array(typecode, [0]) * strides[-1]
            else:
                self._data = array.array(typecode, [0]) * strides[-1]
        else:
            # size = initializer = None
            self._size = (0, 0)
            if is_complex:
                self._real = array.array(typecode, [])
                self._imag = array.array(typecode, [])
            else:
                self._data = array.array(typecode, [])
    self._start = 0


matlab._internal.mlarray_sequence._MLArrayMetaClass.__init__ = mlarray__init__


class ImatestException(_ImatestException):
    pass


class ImatestLibrary(object):
    """

    """
    # Constants
    OP_MODE_STANDARD = 'Standard'
    OP_MODE_SEPARATE = 'Separate'
    OP_MODE_STANDARD_AVERAGE = 'StandardAverage'
    OP_MODE_SIGNAL_AVERAGE = 'SignalAverage'
    OP_MODE_TEMPORAL = 'Temporal'
    OP_MODE_DIRECT_READ = 'DirectRead'

    PIXEL_THRESHOLD_DO_NOT_CALCULATE = 1
    PIXEL_THRESHOLD_ABSOLUTE = 2
    PIXEL_THRESHOLD_RELATIVE = 3

    BLEMISH_ANALYSIS = 1
    CHECKERBOARD_ANALYSIS = 2
    COLORCHECK_ANALYSIS = 3
    DISTORTION_ANALYSIS = 4
    DOTPATTERN_ANALYSIS = 5
    ESFRISO_ANALYSIS = 6
    COLOR_TONE_ANALYSIS = 7
    RANDOM_ANALYSIS = 8
    SFR_ANALYSIS = 9
    SFRPLUS_ANALYSIS = 10
    SFRREG_ANALYSIS = 11
    STAR_ANALYSIS = 12
    UNIFORMITY_ANALYSIS = 13
    WEDGE_ANALYSIS = 14
    LOGFC_ANALYSIS = 15

    PIXEL_SIZE_8_BIT_UNSIGNED = 'B'
    PIXEL_SIZE_16_BIT_UNSIGNED = 'H'
    PIXEL_SIZE_32_BIT_UNSIGNED = 'I'

    # LensType definitions for Geometric Calibrator
    LENS_TYPE_RECTILINEAR = 0 # Use this for lenses that are not fish-eye or relay
    LENS_TYPE_FISH_EYE = 1
    LENS_TYPE_RELAY = 2

    # Dimnsional units used in the TestImage distance_units input parameter
    UNITS_UM = 'um'
    UNITS_MM = 'mm'
    UNITS_CM = 'cm'
    UNITS_M = 'm'
    UNITS_IN = 'in'
    UNITS_FT = 'ft'
    _ALLOWED_UNITS = [UNITS_UM, UNITS_CM, UNITS_FT, UNITS_IN, UNITS_M, UNITS_MM]

    # DeviceSystemType's
    _FIXED_SYSTEM = 0

    # DistortionModelType's
    RADIAL_POLYNOMIAL = 'rad_poly'
    RADIAL_DIVISION_POLYNOMIAL = 'rad_div_poly'
    RADIAL_DIVISION_POLYNOMIAL_PACKED = 'rad_div_poly_packed'
    _ALLOWED_DIST_MODEL_TYPES = [RADIAL_POLYNOMIAL, RADIAL_DIVISION_POLYNOMIAL, RADIAL_DIVISION_POLYNOMIAL_PACKED]

    # PolynomialForm's
    POLY_FORM_EVEN = 'Even'
    POLY_FORM_ODD = 'Odd'
    POLY_FORM_ALL = 'All'
    _ALLOWED_POLY_FORMS = [POLY_FORM_EVEN, POLY_FORM_ODD, POLY_FORM_ALL]

    # TargetType's
    CHECKERBOARD_TARGET_TYPE = 'checkerboard'
    _ALLOW_TARGET_TYPES = [CHECKERBOARD_TARGET_TYPE]

    # TargetDetectionType's
    DETECTION_TYPE_STANDARD = 0
    DETECTION_TYPE_WIDE_FOV = 1
    DETECTION_TYPE_BLURRY = 2

    # CheckerboardType's
    TYPE_1_VARIANT = 1
    TYPE_2_VARIANT = 2
    _ALLOWED_CHART_VARIANTS = [TYPE_1_VARIANT, TYPE_2_VARIANT]

    # Class Members
    lib_imatest_library = None
    version = ''

    # undistort interpolation methods
    INTERPOLATE_LINEAR = 'linear'
    INTERPOLATE_NEAREST = 'nearest'
    INTERPOLATE_SPLINE = 'spline'
    INTERPOLATE_CUBIC = 'cubic'
    INTERPOLATE_MAKIMA = 'makima'
    _ALLOWED_INTERPOLATE = [INTERPOLATE_LINEAR, INTERPOLATE_NEAREST, INTERPOLATE_SPLINE, INTERPOLATE_CUBIC, INTERPOLATE_MAKIMA]

    # Private Constants
    _OP_CODE_STANDARD = '-5'
    _OP_CODE_STANDARD_INI = '-7'
    _OP_CODE_STANDARD_AVG = '-9'
    _OP_CODE_STANDARD_AVG_INI = '-10'
    _OP_CODE_TEMPORAL = '-6'
    _OP_CODE_TEMPORAL_INI = '-8'
    _OP_CODE_DIRECT_READ = '-15'
    _OP_CODE_DIRECT_READ_INI = '-17'

    _ARBITRARY_CHARTS_SEPARATE = '-7'
    _ARBITRARY_CHARTS_SIGNAL_AVERAGE = '-10'
    _ARBITRARY_CHARTS_TEMPORAL = '-8'

    _PARALLEL_ANALYZER_SEPARATE = '-7'
    _PARALLEL_ANALYZER_SIGNAL_AVERAGE = '-10'
    _PARALLEL_ANALYZER_TEMPORAL = '-8'

    _RESULT_JSON = 'JSON'
    _RESULT_JSON_XML = 'JSONXML'

    _MATLAB_RUNTIME_VERSION = '9.8'

    stderr = None
    stdout = None

    def __init__(self, stdout=None, stderr=None):
        # Set up CPU architecture and OS
        self.stdout = stdout
        self.stderr = stderr

        print('Initializing Imatest IT Python Library...', file=self.stdout)

        self._check_library_paths()

        self._load_imatest_library()

        if not self.lib_imatest_library:
            raise ImatestException(message='Could not load Imatest IT Python Library')

        try:
            self.version = self.lib_imatest_library.productversion()
            print('Loaded Imatest IT Python Library %s' % (self.version,), file=self.stdout)
        except Exception:
            raise ImatestException(message='Could not load Imatest IT Python Library')

    def _check_library_paths(self):
        it_bin_in_path = False
        pir = imatest.library._pir
        if not pir:
            raise ImatestException(message='MATLAB libraries were not initialized correctly (missing PIR).')

        lib_filename = ''
        if pir.is_linux:
            lib_filename = 'ShaferFilechck.so'

        if not lib_filename:
            # By pass the search if we don't need to verify the bin path, depends on architecture.
            it_bin_in_path = True
        else:
            if pir.path_var in os.environ:
                path_elements = os.environ[pir.path_var].split(os.pathsep)

                for path in path_elements:
                    if os.path.isfile(os.path.join(path, lib_filename)):
                        it_bin_in_path = True
                        break

        if not it_bin_in_path:
            raise ImatestException(
                message='The Imatest IT "bin" directory must be added to the environment variable "%s". See libs/library/python/readme.txt for details.' % (
                pir.path_var,))

    def _load_imatest_library(self):
        cache_size = 900000000
        # Add environment variables if they do not exist
        more_info_text = r'See http://www.imatest.com/2015/10/best-practices-for-calling-imatest-it-libraries/ for more information. '
        mcr_cache_folder_name = 'mcrCache' + ImatestLibrary._MATLAB_RUNTIME_VERSION
        if 'MCR_CACHE_ROOT' not in os.environ or not os.environ['MCR_CACHE_ROOT']:
            if imatest.library._pir.is_linux:
                mcr_cache_dir = '/var/lib/imatest/mcr_cache'
            else:
                mcr_cache_dir = 'C:\\ProgramData\\Imatest\\mcr_cache\\2020.2\\IT'

            print('**** WARNING ****', file=self.stderr)
            print(
                'Setting the MCR_CACHE_ROOT and MCR_CACHE_SIZE environment variables greatly shortens the load time for the Imatest IT libraries.',
                file=self.stderr)
            print(
                'We recommend setting MCR_CACHE_ROOT to "%s" and MCR_CACHE_SIZE to "%s".' % (mcr_cache_dir, cache_size),
                file=self.stderr)
            print(more_info_text, file=self.stderr)
            print('', file=self.stderr)
            print('', file=self.stderr)
            print('', file=self.stderr)
        elif os.path.isdir(os.environ['MCR_CACHE_ROOT']) and os.path.isfile(
                os.path.join(os.environ['MCR_CACHE_ROOT'], mcr_cache_folder_name, '.max_size')):

            if 'MCR_CACHE_SIZE' in os.environ and os.environ['MCR_CACHE_SIZE'].isdigit():
                with open(os.path.join(os.environ['MCR_CACHE_ROOT'], mcr_cache_folder_name, '.max_size'), 'w') as f:
                    max_size = os.environ['MCR_CACHE_SIZE']
                    f.write(max_size)
            else:
                with open(os.path.join(os.environ['MCR_CACHE_ROOT'], mcr_cache_folder_name, '.max_size'), 'r') as f:
                    max_size = f.read()

            if int(max_size) < cache_size:
                print('**** WARNING ****', file=self.stderr)
                print(
                    'The MCR_CACHE_SIZE environment variable is currently "%s".  To greatly shorten the time it takes for the Imatest IT library to initialize, you should set it to at least "%s"' % (
                    max_size, cache_size), file=self.stderr)
                print(
                    'To fix this, set the environment variable MCR_CACHE_SIZE to "%s" and restart your machine to ensure the change takes effect.' % (
                    cache_size,), file=self.stderr)
                print(more_info_text, file=self.stderr)
                print('', file=self.stderr)
                print('', file=self.stderr)
                print('', file=self.stderr)
        elif 'MCR_CACHE_SIZE' not in os.environ or not os.environ['MCR_CACHE_SIZE'].isdigit():
            print('**** WARNING ****', file=self.stderr)
            print(
                'The MCR_CACHE_SIZE environment variable is not set. To greatly shorten the time it takes for the Imatest IT library to initialize, you should set it to at least "%s".' % (
                cache_size,), file=self.stderr)
            print(more_info_text, file=self.stderr)
            print('', file=self.stderr)
            print('', file=self.stderr)
            print('', file=self.stderr)

        self.lib_imatest_library = imatest.library.initialize()

        if not self.lib_imatest_library:
            raise ImatestException(message='Could not load imatest library.')

    def terminate_library(self):
        if self.lib_imatest_library:
            self.lib_imatest_library.it_terminate(nargout=0)
            self.lib_imatest_library.terminate()

    def close_all_figs(self):
        if self.lib_imatest_library:
            self.lib_imatest_library.close_all_figs(nargout=0)

    def _op_mode_accepts_input_file(self, op_mode):
        return op_mode in (ImatestLibrary.OP_MODE_STANDARD,
                           ImatestLibrary.OP_MODE_SEPARATE,
                           ImatestLibrary.OP_MODE_STANDARD_AVERAGE,
                           ImatestLibrary.OP_MODE_SIGNAL_AVERAGE,
                           ImatestLibrary.OP_MODE_TEMPORAL,)

    def _op_mode_accepts_raw_data(self, op_mode):
        return op_mode in (ImatestLibrary.OP_MODE_DIRECT_READ,)

    def _is_valid_op_mode(self, op_mode):
        return op_mode in (ImatestLibrary.OP_MODE_STANDARD,
                           ImatestLibrary.OP_MODE_SEPARATE,
                           ImatestLibrary.OP_MODE_STANDARD_AVERAGE,
                           ImatestLibrary.OP_MODE_SIGNAL_AVERAGE,
                           ImatestLibrary.OP_MODE_TEMPORAL,
                           ImatestLibrary.OP_MODE_DIRECT_READ,)

    def _op_mode_to_op_code(self, op_mode, has_ini_file):
        if op_mode in (ImatestLibrary.OP_MODE_STANDARD, ImatestLibrary.OP_MODE_SEPARATE):
            return ImatestLibrary._OP_CODE_STANDARD_INI if has_ini_file else ImatestLibrary._OP_CODE_STANDARD
        elif op_mode in (ImatestLibrary.OP_MODE_STANDARD_AVERAGE, ImatestLibrary.OP_MODE_SIGNAL_AVERAGE):
            return ImatestLibrary._OP_CODE_STANDARD_AVG_INI if has_ini_file else ImatestLibrary._OP_CODE_STANDARD_AVG
        elif op_mode == ImatestLibrary.OP_MODE_TEMPORAL:
            return ImatestLibrary._OP_CODE_TEMPORAL_INI if has_ini_file else ImatestLibrary._OP_CODE_TEMPORAL
        elif op_mode == ImatestLibrary.OP_MODE_DIRECT_READ:
            return ImatestLibrary._OP_CODE_DIRECT_READ_INI if has_ini_file else ImatestLibrary._OP_CODE_DIRECT_READ
        else:
            raise ImatestException(message='Invalid Op Mode: "%s"' % (op_mode,))

    def _is_valid_pixel_threshold(self, pixel_threshold):
        return pixel_threshold in (ImatestLibrary.PIXEL_THRESHOLD_DO_NOT_CALCULATE,
                                   ImatestLibrary.PIXEL_THRESHOLD_ABSOLUTE,
                                   ImatestLibrary.PIXEL_THRESHOLD_RELATIVE,)

    def _is_valid_pixel_size(self, pixel_size):
        return pixel_size in (ImatestLibrary.PIXEL_SIZE_8_BIT_UNSIGNED,
                                   ImatestLibrary.PIXEL_SIZE_16_BIT_UNSIGNED,
                                   ImatestLibrary.PIXEL_SIZE_32_BIT_UNSIGNED,)

    def _is_valid_analysis_id(self, analysis_id):
        return analysis_id in (
            ImatestLibrary.BLEMISH_ANALYSIS,
            ImatestLibrary.CHECKERBOARD_ANALYSIS,
            ImatestLibrary.COLORCHECK_ANALYSIS,
            ImatestLibrary.DISTORTION_ANALYSIS,
            ImatestLibrary.DOTPATTERN_ANALYSIS,
            ImatestLibrary.ESFRISO_ANALYSIS,
            ImatestLibrary.COLOR_TONE_ANALYSIS,
            ImatestLibrary.RANDOM_ANALYSIS,
            ImatestLibrary.SFR_ANALYSIS,
            ImatestLibrary.SFRPLUS_ANALYSIS,
            ImatestLibrary.SFRREG_ANALYSIS,
            ImatestLibrary.STAR_ANALYSIS,
            ImatestLibrary.UNIFORMITY_ANALYSIS,
            ImatestLibrary.WEDGE_ANALYSIS,
            ImatestLibrary.LOGFC_ANALYSIS
        )

    def get_arbitrary_charts_options(self, width=None, height=None, encoding=None, filename=None, extension=None, pixel_size=None):
        json_obj = {}

        # Required JSON args
        if width:
            if not isinstance(width, int):
                raise ImatestException(message='JSON arg "width" must be an integer.')
            else:
                json_obj['width'] = width

        if height:
            if not isinstance(height, int):
                raise ImatestException(message='JSON arg "height" must be an integer.')
            else:
                json_obj['height'] = height

        if encoding:
            if not isinstance(encoding, str):
                raise ImatestException(message='JSON arg "encoding" must be a string.')
            else:
                json_obj['encoding'] = encoding
        else:
            raise ImatestException(message='JSON args requires "encoding" parameter.')

        if filename:
            if not isinstance(filename, str):
                raise ImatestException(message='JSON arg "filename" must be a string.')
            else:
                json_obj['fileroot'] = filename

        if extension:
            if not isinstance(extension, str):
                raise ImatestException(message='JSON arg "extension" must be a string.')
            else:
                json_obj['extension'] = extension

        if pixel_size:
            if not isinstance(pixel_size, str):
                raise ImatestException(message='JSON arg "pixel_size" must be a string.')
            elif not self._is_valid_pixel_size(pixel_size):
                raise ImatestException(message='JSON arg "pixel_size" is invalid. Please use one of the constants (i.e., ImatestLibrary.PIXEL_SIZE_8_BIT_UNSIGNED')
            else:
                json_obj['pixel_size'] = pixel_size

        return json_obj

    @staticmethod
    def create_safe_uuid():
        safe_uuid = str(uuid.uuid4())
        safe_uuid = safe_uuid.replace('-', '')
        m = re.search(r"[a-zA-Z]", safe_uuid)
        safe_uuid = safe_uuid[m.start():]

        return safe_uuid

    def get_undistort_options(self, results_folder="", return_unidistorted_arrays=False,
                              image_interpolate_method=INTERPOLATE_LINEAR,  image_extrap_value=None,
                              image_circle=float('Inf'), echo_inputs=False):
        json_obj = {}

        # override the default save location for results
        if not isinstance(results_folder, str):
            raise ImatestException(message='"results_folder" must be a string.')
        else:
            json_obj['results_folder'] = results_folder

        # If true, return the undistorted image arrays, otherwise merely the image file paths for the undistorted images
        if not isinstance(return_unidistorted_arrays, bool):
            raise ImatestException(message='"return_unidistorted_arrays" must be a bool.')
        else:
            json_obj['return_unidistorted_arrays'] = return_unidistorted_arrays

        # Option for how to interpolate the image data. This is not used if undistorting points.
        if image_interpolate_method not in ImatestLibrary._ALLOWED_INTERPOLATE:
            raise ImatestException(message='"distortion_model_type = {0}" is not one of the allowed values: {1}'.format(
                str(image_interpolate_method), ImatestLibrary._ALLOWED_INTERPOLATE))
        else:
            json_obj['image_interpolate_method'] = image_interpolate_method

        # Option for how to extrapolate the image data. This is not used if undistorting points.
        if image_extrap_value is None:
            json_obj['image_extrap_value'] = []
        else:
            if not instance(image_extrap_value, float):
                raise ImatestException(message='"image_extrap_value" must be a float or None.')
            else:
                json_obj['image_extrap_value'] = image_extrap_value

        # The maximum radius from the center of distortion to attempt to undistort. This is to prevent a blowing up of
        # wide FOV distortions (an infinite x infinite array).
        if not instance(image_circle, float):
            raise ImatestException(message='"image_circle" must be a float.')
        else:
            json_obj['image_circle'] = image_circle

        # echo all input contents and data types as received by IT
        if not isinstance(echo_inputs, bool):
            raise ImatestException(message='"echo_inputs" must be a bool.')
        else:
            json_obj['echo_inputs'] = echo_inputs

        return json_obj

    def new_parallel_task(self, image_files=None, image_data=None, analysis_type=None, image_data_meta_data=None):
        json_obj = {}

        if image_files is None and image_data is None:
            raise ImatestException(message='Either "image_files" or "image_data" is required.')

        if image_files is not None and image_data is not None:
            raise ImatestException(message='Only provide one of "image_files" or "image_data", not both.')

        if image_files is not None:
            if not isinstance(image_files, (str, list, tuple)):
                raise ImatestException(message='"image_files" must be either a string, list, or tuple.')
            elif not image_files:
                raise ImatestException(message='"image_files" must not be empty.')
            else:
                json_obj['input'] = image_files

        if image_data is not None:
            if not isinstance(image_data, (str, list, tuple, bytes)):
                raise ImatestException(message='"image_data" must be either a string, bytes, list, or tuple.')
            elif not image_data:
                raise ImatestException(message='"image_data" must not be empty.')

            if image_data_meta_data is None:
                raise ImatestException(
                    message='"image_data_meta_data" is required when using direct read with "image_data".')
            else:
                json_obj['jsonMetadata'] = json.dumps(image_data_meta_data)

            json_obj['input'] = self.__package_image_data(image_data, image_data_meta_data['pixel_size'], False)

        if not analysis_type:
            raise ImatestException(message='"analysis_type" is required.')

        if not self._is_valid_analysis_id(analysis_type):
            raise ImatestException(
                message='"analysis_type" is invalid. Please use the constants (ImatestLibrary.BLEMISH_ANALYSIS, etc.).')

        json_obj['analysisID'] = analysis_type

        return json_obj

    def build_json_args(self, width, height, ncolors, extension, filename=None, crop_borders=None, serial_number=None,
                        part_number=None, lens_to_chart_distance_cm=None, chart_height_cm=None, station=None,
                        operator=None, name=None, operation=None, status=None, hot_pixel_threhold_type=None,
                        dead_pixel_threhold_type=None, hot_pixel_threshold_value_absolute=None,
                        hot_pixel_threshold_value_percentage=None, dead_pixel_threshold_value_absolute=None,
                        dead_pixel_threshold_value_percentage=None, run_blemish_analysis=None,
                        run_uniformity_analysis=None, pixel_size=None):
        json_obj = {}

        # Required JSON args
        if width:
            if not isinstance(width, int):
                raise ImatestException(message='JSON arg "width" must be an integer.')
            else:
                json_obj['width'] = width
        else:
            raise ImatestException(message='JSON args requires "width" parameter.')

        if height:
            if not isinstance(height, int):
                raise ImatestException(message='JSON arg "height" must be an integer.')
            else:
                json_obj['height'] = height
        else:
            raise ImatestException(message='JSON args requires "height" parameter.')

        if ncolors:
            if not isinstance(ncolors, int):
                raise ImatestException(message='JSON arg "ncolors" must be an integer.')
            else:
                json_obj['ncolors'] = ncolors
        else:
            raise ImatestException(message='JSON args requires "ncolors" parameter.')

        if extension:
            if not isinstance(extension, str):
                raise ImatestException(message='JSON arg "extension" must be a string.')
            else:
                json_obj['extension'] = extension
        else:
            raise ImatestException(message='JSON args requires "extension" parameter.')

        if filename:
            if not isinstance(filename, str):
                raise ImatestException(message='JSON arg "filename" must be a string.')
            else:
                json_obj['fileroot'] = filename

        # Option JSON args
        if crop_borders:
            if not isinstance(crop_borders, (list, tuple)):
                raise ImatestException(message='JSON arg "crop_borders" must be a list or tuple.')
            else:
                if len(crop_borders) != 4:
                    raise ImatestException(message='JSON arg "crop_borders" must contain four numbers.')

                if not all(isinstance(item, (int, float)) for item in crop_borders):
                    raise ImatestException(message='All items in "crop_borders" JSON arg must be numbers.')

                json_obj['crop_borders'] = crop_borders

        if serial_number:
            json_obj['serial_number'] = serial_number

        if part_number:
            json_obj['part_number'] = part_number

        if lens_to_chart_distance_cm:
            if not isinstance(lens_to_chart_distance_cm, (int, float)):
                raise ImatestException(message='JSON arg "lens_to_chart_distance_cm" must be a number.')

            json_obj['lens_to_chart_distance_cm'] = lens_to_chart_distance_cm

        if chart_height_cm:
            if not isinstance(chart_height_cm, (int, float)):
                raise ImatestException(message='JSON arg "chart_height_cm" must be a number.')

            json_obj['chart_height_cm'] = chart_height_cm

        if station:
            json_obj['station'] = station
        if operator:
            json_obj['operator'] = operator
        if name:
            json_obj['name'] = name
        if operation:
            json_obj['operation'] = operation
        if status:
            json_obj['status'] = status
        if part_number:
            json_obj['part_number'] = part_number

        if hot_pixel_threhold_type:
            if not self._is_valid_pixel_threshold(hot_pixel_threhold_type):
                raise ImatestException(message='Invalid value for "hot_pixel_threhold_type".')
            json_obj['hot_pixel_type'] = hot_pixel_threhold_type

        if dead_pixel_threhold_type:
            if not self._is_valid_pixel_threshold(dead_pixel_threhold_type):
                raise ImatestException(message='Invalid value for "dead_pixel_threhold_type".')
            json_obj['dead_pixel_type'] = dead_pixel_threhold_type

        if hot_pixel_threshold_value_absolute is not None or hot_pixel_threshold_value_percentage is not None:
            if hot_pixel_threshold_value_absolute is None:
                hot_pixel_threshold_value_absolute = 0
            if hot_pixel_threshold_value_percentage is None:
                hot_pixel_threshold_value_percentage = 0
            json_obj['hot_pixel_thresholds'] = [hot_pixel_threshold_value_absolute,
                                                hot_pixel_threshold_value_percentage]

        if dead_pixel_threshold_value_absolute is not None or dead_pixel_threshold_value_percentage is not None:
            if dead_pixel_threshold_value_absolute is None:
                dead_pixel_threshold_value_absolute = 0
            if dead_pixel_threshold_value_percentage is None:
                dead_pixel_threshold_value_percentage = 0
            json_obj['dead_pixel_thresholds'] = [dead_pixel_threshold_value_absolute,
                                                 dead_pixel_threshold_value_percentage]

        if run_blemish_analysis is not None:
            if run_blemish_analysis:
                run_blemish_analysis = 1
            else:
                run_blemish_analysis = 0
            json_obj['blemish_analysis'] = run_blemish_analysis

        if run_uniformity_analysis is not None:
            if run_uniformity_analysis:
                run_uniformity_analysis = 1
            else:
                run_uniformity_analysis = 0
            json_obj['uniformity_analysis'] = run_uniformity_analysis

        if not pixel_size:
            pixel_size = ImatestLibrary.PIXEL_SIZE_16_BIT_UNSIGNED

        if pixel_size:
            if not isinstance(pixel_size, str):
                raise ImatestException(message='JSON arg "pixel_size" must be a string.')
            elif not self._is_valid_pixel_size(pixel_size):
                raise ImatestException(message='JSON arg "pixel_size" is invalid. Please use one of the constants (i.e., ImatestLibrary.PIXEL_SIZE_8_BIT_UNSIGNED')
            else:
                json_obj['pixel_size'] = pixel_size

        return json_obj

    def _process(self, library_method_name, input_file=None, root_dir=None, input_keys=None, op_mode=None,
                 ini_file=None, raw_image=None, json_args=None):

        if not self._is_valid_op_mode(op_mode):
            raise ImatestException(message='Invalid "op_mode" parameter.')

        if self._op_mode_accepts_input_file(op_mode):
            if not input_file:
                raise ImatestException(message='"input_file" parameter is required for this op mode.')

            if isinstance(input_file, str):
                input_file = [input_file]

            if not isinstance(input_file, list):
                raise ImatestException(message='"input_file" parameter must be a string or a list of strings."')

        varg_in_count = 0
        has_multiple_images = False
        has_direct_read = False
        has_ini_file = False

        if ini_file:
            # Validate ini file is passed in exists
            if not os.path.isfile(ini_file):
                raise ImatestException(message='Could not find .ini file at "%s".' % ini_file)

            has_ini_file = True
            varg_in_count += 1

        if self._op_mode_accepts_input_file(op_mode):
            if len(input_file) > 1:
                # In this case, we have multiple images to be processed
                varg_in_count += (len(input_file) - 1)
                has_multiple_images = True
            else:
                # Only processing a single file
                input_file = input_file[0]

        if self._op_mode_accepts_raw_data(op_mode):
            if not raw_image:
                raise ImatestException(
                    message='Please pass a valid "raw_image" parameter when using op_code "%s"' % op_mode)
            if not json_args:
                raise ImatestException(
                    message='Please pass a valid "json_args" parameter when using op_code "%s"' % op_mode)

            has_direct_read = True
            varg_in_count += 2

        if varg_in_count > 0:
            mx_varg_in = []

            if has_ini_file:
                mx_varg_in.append(ini_file)

            if has_multiple_images:
                for image in input_file[1:]:
                    mx_varg_in.append(image)

                input_file = input_file[0]
            elif has_direct_read:
                mx_raw = self.__package_image_data(raw_image, json_args['pixel_size'], False)
                mx_varg_in.append(mx_raw)
                mx_varg_in.append(json.dumps({"jstr": json_args}))
        else:
            mx_varg_in = None

        op_code = self._op_mode_to_op_code(op_mode, has_ini_file)

        library_method = getattr(self.lib_imatest_library, '%s_shell' % library_method_name)

        # MATLAB will not allow us to pass in 'None' values, must replace with empty string
        # Replace 'None' arguments with empty string
        if input_file is None:
            input_file = ''

        if root_dir is None:
            root_dir = ''

        result = None
        try:
            if mx_varg_in:
                result = library_method(input_file,
                                        root_dir,
                                        input_keys,
                                        op_code,
                                        *mx_varg_in,
                                        stdout=self.stdout,
                                        stderr=self.stderr)
            else:
                result = library_method(input_file,
                                        root_dir,
                                        input_keys,
                                        op_code,
                                        stdout=self.stdout,
                                        stderr=self.stderr)
        except MatlabRuntimeError as mre:
            (error_id, error_name) = self.lib_imatest_library.getExceptionID(nargout=2)
            if isinstance(error_name, list) and len(error_name) > 0:
                raise ImatestException(error_id=int(error_id), error_name=error_name[0], message=str(mre))
            else:
                raise ImatestException(error_id=int(error_id), error_name=error_name, message=str(mre))
        except Exception as e:
            raise ImatestException(message=str(e))

        if result is None:
            raise ImatestException(message="An error occurred calling %s." % (library_method_name,))

        return result

    def ois(self, unshaken_json_path=None, shaken_ois_off_json_path=None, shaken_ois_on_json_path=None,
            pass_fail_path=None):
        if not unshaken_json_path or not shaken_ois_off_json_path or not shaken_ois_on_json_path:
            raise ImatestException(message=
                                   'All three input json strings are required, "unshaken_json_path", "shaken_ois_off_json_path", and "shaken_ois_off_path".')

        if pass_fail_path:
            if not isinstance(pass_fail_path, str):
                raise ImatestException(message='"pass_fail_path" parameter must be a string.')

            if not os.path.exists(pass_fail_path):
                raise ImatestException(message='Cannot find pass fail file at "%s".' % (pass_fail_path,))

                mx_pass_fail_path = None

        # NOTE: OIS crashes if None is passed for pass_fail, so send an empty string if no pass/fail file.
        if pass_fail_path is None:
            pass_fail_path = ''

        result = None
        try:
            result = self.lib_imatest_library.ois_shell('1',
                                                        unshaken_json_path,
                                                        shaken_ois_off_json_path,
                                                        shaken_ois_on_json_path,
                                                        pass_fail_path,
                                                        stdout=self.stdout,
                                                        stderr=self.stderr)
        except MatlabRuntimeError as mre:
            (error_id, error_name) = self.lib_imatest_library.getExceptionID(nargout=2)
            if isinstance(error_name, list) and len(error_name) > 0:
                raise ImatestException(int(error_id), error_name[0])
            else:
                raise ImatestException(int(error_id), error_name)
        except Exception as e:
            raise ImatestException(message=str(e))

        if not result:
            raise ImatestException(message="An error occurred calling ois.")

        return result

    def __package_image_data(self, image_data, pixel_size_code, allow_list=False):
        if isinstance(image_data, (list, tuple)) and allow_list:
            image_data_list = []
            for image in image_data:
                image_data_list.append(self.__package_image_data(image, False))
            return image_data_list

        if pixel_size_code == self.PIXEL_SIZE_8_BIT_UNSIGNED:
            mx_raw = matlab.uint8()
        elif pixel_size_code == self.PIXEL_SIZE_16_BIT_UNSIGNED:
            mx_raw = matlab.uint16()
        elif pixel_size_code == self.PIXEL_SIZE_32_BIT_UNSIGNED:
            mx_raw = matlab.uint32()
        else:
            raise ImatestException(message="Invalid 'pixel_size' argument: %s" % pixel_size_code)

        if isinstance(image_data, (str, bytes)):
            # String was passed in
            mx_raw_array = array.array(pixel_size_code)
            mx_raw_array.fromstring(image_data)

            arr_len = len(mx_raw_array)
            mx_raw._size = (1, arr_len)
            mx_raw._strides = [1, 1]
            mx_raw._data = mx_raw_array

            return mx_raw
        elif isinstance(image_data, array.array):
            # array.array was passed in

            arr_len = len(image_data)
            mx_raw._size = (1, arr_len)
            mx_raw._strides = [1, 1]
            mx_raw._data = image_data

            return mx_raw
        else:
            raise ImatestException(
                message="Invalid type for parameter raw_image: %s. Valid types are <str>, <bytes>, and <array.array>." % type(
                    image_data))

    def __arbitrary_charts(self, image_files=None, image_data=None, chart_file=None, ini_file=None, options=None,
                           op_code=None):
        result = None
        input = None

        # Validate options
        if not options:
            raise ImatestException(
                message='The "options" argument is required. Use ImatestLibrary.get_arbitrary_charts_options() to produce it.')

            if not isinstance(options, dict):
                raise ImatestException(
                    message='The "options" parameter must be a Dictionary. Use ImatestLibrary.get_arbitrary_charts_options() to produce it.')

            if 'encoding' not in options or not options['encoding']:
                raise ImatestException(message='The "encoding" parameter in "options" is required.')

        # Validate image_file or image_data is present
        if (image_files is None) and (image_data is None):
            raise ImatestException(message='Either the "image_files" or "image_data" parameter is required.')

        if image_files and image_data:
            raise ImatestException(message='Pass in either "image_files" or "image_data", but not both.')

        # Validate image_file
        if image_files is not None:
            if isinstance(image_files, (list, tuple)):
                if len(image_files) == 0:
                    raise ImatestException(message='The "image_files" argument must contain at least one image path.')

                if op_code == self._ARBITRARY_CHARTS_SIGNAL_AVERAGE and len(image_files) == 1:
                    raise ImatestException(
                        message='The "image_files" argument must contain at least two images.  For single image analysis, use the arbitrary_charts function.')

                for file_path in image_files:
                    if not os.path.isfile(file_path):
                        raise ImatestException(message='Could not find image file at "%s".' % file_path)
            else:
                if image_files == '':
                    raise ImatestException(message='The "image_files" parameter cannot be empty.'
                                           )
                if op_code in (self._ARBITRARY_CHARTS_SIGNAL_AVERAGE, self._ARBITRARY_CHARTS_TEMPORAL):
                    raise ImatestException(message='The "image_files" argument must be a list or tuple.')

                if not os.path.isfile(image_files):
                    raise ImatestException(message='Could not find image file at "%s".' % image_files)
            input = image_files

        # Validate image_data
        if image_data is not None:
            if 'height' not in options or options['height'] <= 0:
                raise ImatestException(
                    message='The "height" parameter in "options" is required and must be greater than 0.')

            if 'width' not in options or options['width'] <= 0:
                raise ImatestException(
                    message='The "width" parameter in "options" is required and must be greater than 0.')
            if 'fileroot' not in options or not options['fileroot']:
                raise ImatestException(
                    message='The "filename" parameter in "options" is required when using Direct Read Mode.')
            if 'extension' not in options or not options['extension']:
                raise ImatestException(
                    message='The "extension" parameter in "options" is required when using Direct Read Mode.')

            if 'pixel_size' not in options or not options['pixel_size']:
                raise ImatestException(
                    message='The "pixel_size" parameter in "options" is required when using Direct Read Mode.')

            if not self._is_valid_pixel_size(options['pixel_size']):
                raise ImatestException(
                    message='The "pixel_size" parameter in "options" is invalid. Please use the constants (ImatestLibrary.PIXEL_SIZE_8_BIT_UNSIGNED, etc.).')

            if isinstance(image_data, (list, tuple)):
                if len(image_data) == 0:
                    raise ImatestException(message='The "image_data" argument must contain at least one image.')

            if op_code == self._ARBITRARY_CHARTS_SIGNAL_AVERAGE and len(image_data) == 1:
                raise ImatestException(
                    message='The "image_data" argument must contain at least two images.  For single image analysis, use the arbitrary_charts function.')

            input = self.__package_image_data(image_data, options['pixel_size'], True)

        # Validate chart_file
        if not chart_file:
            raise ImatestException(message='The "chart_file" argument is required.')

        # Make sure chart file exists
        if not os.path.isfile(chart_file):
            raise ImatestException(message='Could not find chart definition .json file at "%s".' % ini_file)

        # Validate ini_file
        if not ini_file:
            raise ImatestException(message='The "ini_file" argument is required.')

        # Make sure ini file exists
        if not os.path.isfile(ini_file):
            raise ImatestException(message='Could not find .ini file at "%s".' % ini_file)





        try:
            result = self.lib_imatest_library.arbitrary_charts_shell(input, chart_file, ini_file, op_code,
                                                                     json.dumps(options),
                                                                     stdout=self.stdout,
                                                                     stderr=self.stderr)
        except MatlabRuntimeError as mre:
            (error_id, error_name) = self.lib_imatest_library.getExceptionID(nargout=2)
            if isinstance(error_name, list) and len(error_name) > 0:
                raise ImatestException(int(error_id), error_name[0])
            else:
                raise ImatestException(int(error_id), error_name)
        except Exception as e:
            raise ImatestException(message=str(e))

        if not result:
            raise ImatestException(message="An error occurred calling ois.")

        return result

    def arbitrary_charts_separate(self, image_files=None, image_data=None, chart_file=None, ini_file=None,
                                  options=None):
        return self.__arbitrary_charts(image_files=image_files, image_data=image_data, chart_file=chart_file,
                                       ini_file=ini_file, options=options, op_code=self._ARBITRARY_CHARTS_SEPARATE)

    def arbitrary_charts_signal_average(self, image_files=None, image_data=None, chart_file=None, ini_file=None,
                                        options=None):
        return self.__arbitrary_charts(image_files=image_files, image_data=image_data, chart_file=chart_file,
                                       ini_file=ini_file, options=options,
                                       op_code=self._ARBITRARY_CHARTS_SIGNAL_AVERAGE)

    # def arbitrary_charts_temporal(self, image_files=None, image_data=None, chart_file=None, ini_file=None, options=None):
    #     return self.__arbitrary_charts(image_files=image_files, image_data=image_data, chart_file=chart_file, ini_file=ini_file, options=options, op_code=self._ARBITRARY_CHARTS_TEMPORAL)


    def __undistort(self, distortion_component, ini_file, options):
        try:
            result = self.lib_imatest_library.undistor_shell(json.dumps(distortionComponent), ini_file,
                                                                         json.dumps(options),
                                                                         stdout=self.stdout,
                                                                         stderr=self.stderr)
        except MatlabRuntimeError as mre:
            (error_id, error_name) = self.lib_imatest_library.getExceptionID(nargout=2)
            if isinstance(error_name, list) and len(error_name) > 0:
                raise ImatestException(int(error_id), error_name[0])
            else:
                raise ImatestException(int(error_id), error_name)
        except Exception as e:
            raise ImatestException(message=str(e))

        if not result:
            raise ImatestException(message="An error occurred calling geometric_calibrator.")

        return result

    def undistort(self, distortion_component, ini_file, options):
        return self.__undistort(distortion_component=distortion_component, ini_file=ini_file, options=options)

    def __parallel_analyzer(self, tasks, ini_file, run_parallel, num_workers, op_code):

        # ADD VALIDATIONS:
        # tasks needs to be a list

        # result = None
        # input = None
        # # Validate image_file or image_data is present
        # if (image_files is None) and (image_data is None):
        #     raise ImatestException(message='Either the "image_files" or "image_data" parameter is required.')
        #
        # if image_files and image_data:
        #     raise ImatestException(message='Pass in either "image_files" or "image_data", but not both.')
        #
        # # Validate image_file
        # if image_files is not None:
        #     if isinstance(image_files, (list, tuple)):
        #         if len(image_files) == 0:
        #             raise ImatestException(message='The "image_files" argument must contain at least one image path.')
        #
        #         if op_code == self._ARBITRARY_CHARTS_SIGNAL_AVERAGE and len(image_files) == 1:
        #             raise ImatestException(
        #                 message='The "image_files" argument must contain at least two images.  For single image analysis, use the arbitrary_charts function.')
        #
        #         for file_path in image_files:
        #             if not os.path.isfile(file_path):
        #                 raise ImatestException(message='Could not find image file at "%s".' % file_path)
        #     else:
        #         if image_files == '':
        #             raise ImatestException(message='The "image_files" parameter cannot be empty.'
        #                                    )
        #         if op_code in (self._ARBITRARY_CHARTS_SIGNAL_AVERAGE, self._ARBITRARY_CHARTS_TEMPORAL):
        #             raise ImatestException(message='The "image_files" argument must be a list or tuple.')
        #
        #         if not os.path.isfile(image_files):
        #             raise ImatestException(message='Could not find image file at "%s".' % image_files)
        #     input = image_files
        # # Validate image_data
        # if image_data is not None:
        #     if isinstance(image_data, (list, tuple)):
        #         if len(image_data) == 0:
        #             raise ImatestException(message='The "image_data" argument must contain at least one image.')
        #
        #     if op_code == self._ARBITRARY_CHARTS_SIGNAL_AVERAGE and len(image_data) == 1:
        #         raise ImatestException(
        #             message='The "image_data" argument must contain at least two images.  For single image analysis, use the arbitrary_charts function.')
        #
        #     input = image_data
        #
        # # Validate chart_file
        # if not chart_file:
        #     raise ImatestException(message='The "chart_file" argument is required.')
        #
        # # Make sure chart file exists
        # if not os.path.isfile(chart_file):
        #     raise ImatestException(message='Could not find chart definition .json file at "%s".' % ini_file)
        #
        # # Validate ini_file
        # if not ini_file:
        #     raise ImatestException(message='The "ini_file" argument is required.')
        #
        # # Make sure ini file exists
        # if not os.path.isfile(ini_file):
        #     raise ImatestException(message='Could not find .ini file at "%s".' % ini_file)
        #
        # # Validate options
        # if not options:
        #     raise ImatestException(
        #         message='The "options" argument is required. Use ImatestLibrary.get_arbitrary_charts_options() to produce it.')
        #
        #     if not isinstance(options, dict):
        #         raise ImatestException(
        #             message='The "options" parameter must be a Dictionary. Use ImatestLibrary.get_arbitrary_charts_options() to produce it.')
        #
        #
        #
        #     if 'encoding' not in options or not options['encoding']:
        #         raise ImatestException(message='The "encoding" parameter in "options" is required.')
        #
        # # TODO:  Enum encoding.
        # if image_data:
        #     if 'height' not in options or options['height'] <= 0:
        #         raise ImatestException(
        #             message='The "height" parameter in "options" is required and must be greater than 0.')
        #
        #     if 'width' not in options or options['width'] <= 0:
        #         raise ImatestException(
        #             message='The "width" parameter in "options" is required and must be greater than 0.')
        #     if 'fileroot' not in options or not options['fileroot']:
        #         raise ImatestException(
        #             message='The "filename" parameter in "options" is required when using Direct Read Mode.')
        #     if 'extension' not in options or not options['extension']:
        #         raise ImatestException(
        #             message='The "extension" parameter in "options" is required when using Direct Read Mode.')

        try:
            result = self.lib_imatest_library.parallel_analyzer_shell(tasks, ini_file, run_parallel,
                                                                      num_workers,
                                                                      stdout=self.stdout,
                                                                      stderr=self.stderr)
        except MatlabRuntimeError as mre:
            (error_id, error_name) = self.lib_imatest_library.getExceptionID(nargout=2)
            if isinstance(error_name, list) and len(error_name) > 0:
                raise ImatestException(int(error_id), error_name[0])
            else:
                raise ImatestException(int(error_id), error_name)
        except Exception as e:
            raise ImatestException(message=str(e))

        if not result:
            raise ImatestException(message="An error occurred calling parallel_analyzer.")

        return result

    def parallel_analyzer(self, tasks=None, ini_file=None, run_parallel=True, num_workers=1):
        return self.__parallel_analyzer(tasks=tasks, ini_file=ini_file, run_parallel=run_parallel,
                                        num_workers=num_workers, op_code=self._PARALLEL_ANALYZER_SEPARATE)

    # def parallel_analyzer_separate(self, tasks=None, ini_file=None, run_parallel=True, num_workers=1):
    #     return self.__parallel_analyzer(tasks=tasks, ini_file=ini_file, run_parallel=run_parallel,
    #                                     num_workers=num_workers, op_code=self._PARALLEL_ANALYZER_SEPARATE)
    #
    # def parallel_analyzer_signal_average(self, tasks=None, ini_file=None, run_parallel=True, num_workers=1):
    #     return self.__parallel_analyzer(tasks=tasks, ini_file=ini_file, run_parallel=run_parallel,
    #                                     num_workers=num_workers, op_code=self._PARALLEL_ANALYZER_SIGNAL_AVERAGE)
    #
    # def parallel_analyzer_temporal(self, tasks=None, ini_file=None, run_parallel=True, num_workers=1):
    #     return self.__parallel_analyzer(tasks=tasks, ini_file=ini_file, run_parallel=run_parallel,
    #                                     num_workers=num_workers, op_code=self._PARALLEL_ANALYZER_TEMPORAL)

    def blemish(self, input_file=None, root_dir=None, op_mode=None, ini_file=None, raw_data=None,
                     json_args=None):
        return self._process('blemish', input_file, root_dir, ImatestLibrary._RESULT_JSON, op_mode, ini_file, raw_data,
                             json_args)

    def blemish_json(self, input_file=None, root_dir=None, op_mode=None, ini_file=None, raw_data=None,
                     json_args=None):
        return self.blemish(input_file=input_file, root_dir=root_dir, op_mode=op_mode, ini_file=ini_file, raw_data=raw_data,
                             json_args=json_args)

    def checkerboard(self, input_file=None, root_dir=None, op_mode=None, ini_file=None, raw_data=None,
                          json_args=None):
        return self._process('checkerboard', input_file, root_dir, ImatestLibrary._RESULT_JSON, op_mode, ini_file,
                             raw_data, json_args)

    def checkerboard_json(self, input_file=None, root_dir=None, op_mode=None, ini_file=None, raw_data=None,
                          json_args=None):
        return self.checkerboard(input_file=input_file, root_dir=root_dir, op_mode=op_mode, ini_file=ini_file,
                             raw_data=raw_data, json_args=json_args)

    def colorcheck(self, input_file=None, root_dir=None, op_mode=None, ini_file=None, raw_data=None,
                        json_args=None):
        return self._process('colorcheck', input_file, root_dir, ImatestLibrary._RESULT_JSON, op_mode, ini_file,
                             raw_data, json_args)

    def colorcheck_json(self, input_file=None, root_dir=None, op_mode=None, ini_file=None, raw_data=None,
                        json_args=None):
        return self.colorcheck(input_file=input_file, root_dir=root_dir, op_mode=op_mode, ini_file=ini_file,
                             raw_data=raw_data, json_args=json_args)

    def distortion(self, input_file=None, root_dir=None, op_mode=None, ini_file=None, raw_data=None,
                        json_args=None):
        return self._process('distortion', input_file, root_dir, ImatestLibrary._RESULT_JSON, op_mode, ini_file,
                             raw_data, json_args)

    def distortion_json(self, input_file=None, root_dir=None, op_mode=None, ini_file=None, raw_data=None,
                        json_args=None):
        return self.distortion(input_file=input_file, root_dir=root_dir, op_mode=op_mode, ini_file=ini_file,
                             raw_data=raw_data, json_args=json_args)

    def dotpattern(self, input_file=None, root_dir=None, op_mode=None, ini_file=None, raw_data=None,
                        json_args=None):
        return self._process('dotpattern', input_file, root_dir, ImatestLibrary._RESULT_JSON, op_mode, ini_file,
                             raw_data, json_args)

    def dotpattern_json(self, input_file=None, root_dir=None, op_mode=None, ini_file=None, raw_data=None,
                        json_args=None):
        return self.dotpattern(input_file=input_file, root_dir=root_dir, op_mode=op_mode, ini_file=ini_file,
                             raw_data=raw_data, json_args=json_args)

    def esfriso(self, input_file=None, root_dir=None, op_mode=None, ini_file=None, raw_data=None,
                     json_args=None):
        return self._process('esfriso', input_file, root_dir, ImatestLibrary._RESULT_JSON, op_mode, ini_file, raw_data,
                             json_args)

    def esfriso_json(self, input_file=None, root_dir=None, op_mode=None, ini_file=None, raw_data=None,
                     json_args=None):
        return self.esfriso(input_file=input_file, root_dir=root_dir, op_mode=op_mode, ini_file=ini_file, raw_data=raw_data,
                             json_args=json_args)

    def logfc(self, input_file=None, root_dir=None, op_mode=None, ini_file=None, raw_data=None,
                  json_args=None):
        return self._process('logfc', input_file, root_dir, ImatestLibrary._RESULT_JSON, op_mode, ini_file, raw_data,
                             json_args)

    def logfc_json(self, input_file=None, root_dir=None, op_mode=None, ini_file=None, raw_data=None,
                  json_args=None):
        return self.logfc(input_file=input_file, root_dir=root_dir, op_mode=op_mode, ini_file=ini_file, raw_data=raw_data,
                             json_args=json_args)

    def color_tone(self, input_file=None, root_dir=None, op_mode=None, ini_file=None, raw_data=None,
                       json_args=None):
        return self._process('color_tone', input_file, root_dir, ImatestLibrary._RESULT_JSON, op_mode, ini_file,
                             raw_data, json_args)

    def color_tone_json(self, input_file=None, root_dir=None, op_mode=None, ini_file=None, raw_data=None,
                       json_args=None):
        return self.color_tone(input_file=input_file, root_dir=root_dir, op_mode=op_mode, ini_file=ini_file,
                             raw_data=raw_data, json_args=json_args)

    def random(self, input_file=None, root_dir=None, op_mode=None, ini_file=None, raw_data=None,
                    json_args=None):
        return self._process('random', input_file, root_dir, ImatestLibrary._RESULT_JSON, op_mode, ini_file, raw_data,
                             json_args)

    def random_json(self, input_file=None, root_dir=None, op_mode=None, ini_file=None, raw_data=None,
                    json_args=None):
        return self.random(input_file=input_file, root_dir=root_dir, op_mode=op_mode, ini_file=ini_file, raw_data=raw_data,
                             json_args=json_args)

    def sfr(self, input_file=None, root_dir=None, op_mode=None, ini_file=None, raw_data=None,
                 json_args=None):
        return self._process('sfr', input_file, root_dir, ImatestLibrary._RESULT_JSON, op_mode, ini_file, raw_data,
                             json_args)

    def sfr_json(self, input_file=None, root_dir=None, op_mode=None, ini_file=None, raw_data=None,
                 json_args=None):
        return self.sfr(input_file=input_file, root_dir=root_dir, op_mode=op_mode, ini_file=ini_file, raw_data=raw_data,
                             json_args=json_args)

    def sfrplus(self, input_file=None, root_dir=None, op_mode=None, ini_file=None, raw_data=None,
                     json_args=None):
        return self._process('sfrplus', input_file, root_dir, ImatestLibrary._RESULT_JSON, op_mode, ini_file, raw_data,
                             json_args)

    def sfrplus_json(self, input_file=None, root_dir=None, op_mode=None, ini_file=None, raw_data=None,
                     json_args=None):
        return self.sfrplus(input_file=input_file, root_dir=root_dir, op_mode=op_mode, ini_file=ini_file, raw_data=raw_data,
                             json_args=json_args)

    def sfrreg(self, input_file=None, root_dir=None, op_mode=None, ini_file=None, raw_data=None,
                    json_args=None):
        return self._process('sfrreg', input_file, root_dir, ImatestLibrary._RESULT_JSON, op_mode, ini_file, raw_data,
                             json_args)

    def sfrreg_json(self, input_file=None, root_dir=None, op_mode=None, ini_file=None, raw_data=None,
                    json_args=None):
        return self.sfrreg(input_file=input_file, root_dir=root_dir, op_mode=op_mode, ini_file=ini_file, raw_data=raw_data,
                             json_args=json_args)

    def star(self, input_file=None, root_dir=None, op_mode=None, ini_file=None, raw_data=None,
                  json_args=None):
        return self._process('star', input_file, root_dir, ImatestLibrary._RESULT_JSON, op_mode, ini_file, raw_data,
                             json_args)

    def star_json(self, input_file=None, root_dir=None, op_mode=None, ini_file=None, raw_data=None,
                  json_args=None):
        return self.star(input_file=input_file, root_dir=root_dir, op_mode=op_mode, ini_file=ini_file, raw_data=raw_data,
                             json_args=json_args)

    def stepchart(self, input_file=None, root_dir=None, op_mode=None, ini_file=None, raw_data=None,
                       json_args=None):
        return self._process('stepchart', input_file, root_dir, ImatestLibrary._RESULT_JSON, op_mode, ini_file,
                             raw_data, json_args)

    def stepchart_json(self, input_file=None, root_dir=None, op_mode=None, ini_file=None, raw_data=None,
                       json_args=None):
        return self.stepchart(input_file=input_file, root_dir=root_dir, op_mode=op_mode, ini_file=ini_file,
                             raw_data=raw_data, json_args=json_args)

    def uniformity(self, input_file=None, root_dir=None, op_mode=None, ini_file=None, raw_data=None,
                        json_args=None):
        return self._process('uniformity', input_file, root_dir, ImatestLibrary._RESULT_JSON, op_mode, ini_file,
                             raw_data, json_args)

    def uniformity_json(self, input_file=None, root_dir=None, op_mode=None, ini_file=None, raw_data=None,
                        json_args=None):
        return self.uniformity(input_file=input_file, root_dir=root_dir, op_mode=op_mode, ini_file=ini_file,
                             raw_data=raw_data, json_args=json_args)

    def wedge(self, input_file=None, root_dir=None, op_mode=None, ini_file=None, raw_data=None,
                   json_args=None):
        return self._process('wedge', input_file, root_dir, ImatestLibrary._RESULT_JSON, op_mode, ini_file, raw_data,
                             json_args)

    def wedge_json(self, input_file=None, root_dir=None, op_mode=None, ini_file=None, raw_data=None,
                   json_args=None):
        return self.wedge(input_file=input_file, root_dir=root_dir, op_mode=op_mode, ini_file=ini_file, raw_data=raw_data,
                             json_args=json_args)
