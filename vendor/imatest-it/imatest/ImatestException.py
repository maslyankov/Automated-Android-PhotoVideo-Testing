

class _ImatestException(Exception):
    error_id = None
    error_name = None

    def __init__(self, error_id=None, error_name=None, message=None):
        self.error_id = error_id
        self.error_name = error_name
        self.message = message

    AutoDetectException = -100
    BadFramingException = -101
    BadImageSizeException = -102
    ChartDesignException = -103
    ColorConversionException = -104
    ConfigurationException = -105
    CropException = -106
    DBConnectionException = -107
    DataConstructorException = -108
    DataException = -109
    DatabaseException = -110
    DetectionException = -111
    EarlyNullTerminationException = -112
    EmptyImageException = -113
    ImageAcquisitionException = -114
    ImageAnalysisException = -115
    ImageException = -116
    ImageSourceException = -117
    ImatestCannotOpenFileException = -118
    ImatestException = -119
    ImatestFileNotFoundException = -120
    ImatestIOException = -121
    ImatestSocketException = -122
    IncorrectNumInputsException = -123
    IncorrectNumOutputsException = -124
    InputFormatException = -125
    JsonException = -126
    LicenseException = -127
    OutputException = -128
    ParameterException = -129
    PlottingException = -130
    QueryException = -131
    RoiFailureException = -132
    UIException = -133
    UnsupportedFormatException = -134
    UnsupportedTypeException = -135
    UserCancelException = -136
    VideoException = -137
    WrongInputTypeException = -138
    XmlException = -139
    FloatingLicenseException = -140
    UnknownException = -555
    MatlabException = -999

