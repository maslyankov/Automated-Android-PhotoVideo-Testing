Packaging and Deploying imatest.it

1. Prerequisites for Deployment 

A. If MATLAB Runtime version 9.0.1 (R2016a) has not been installed, install it in one of 
   these ways:

i. Run the package installer, which will also install the MATLAB Runtime.
NOTE: You will need administrator rights to run the installer. 

ii. Download the Windows 64-bit version of the MATLAB Runtime for R2016a from:

    http://www.mathworks.com/products/compiler/mcr/index.html
   
iii. Run the MATLAB Runtime installer provided with MATLAB.

B. Verify that a Windows 64-bit version of Python 2.7, 3.3, and/or 3.4 is installed.

2. Installing the imatest.it Package

A. Go to the directory that contains the file setup.py and the subdirectory imatest (<IMATEST_ROOT>\libs\library\python). If 
   you do not have write permissions, copy all its contents to a temporary location and 
   go there.

B. Execute the command:

    python setup.py install [options]
    
If you have full administrator privileges, and install to the default location, you do 
   not need to specify any options. Otherwise, use --user to install to your home folder, 
   or --prefix="installdir" to install to "installdir". In the latter case, add 
   "installdir" to the PYTHONPATH environment variable. For details, refer to:

    https://docs.python.org/2/install/index.html


3. Using the imatest.it Package

The library package is on your Python path. To import it into a Python script or session, 
   simply execute:

    from imatest.it import ImatestLibrary

To make calls to Imatest IT, first create a library object.  Because there is some overhead while initializing the MATLAB Runtime, it is best to only create one instance per session.

    imatest = ImatestLibrary()

You can use this object to make calls to the various Imatest IT modules (see the sample code for specific examples for each module in <IMATEST_ROOT>\samples\python).

When you are finished using the library, be sure to terminate the library object.
  
    imatest.terminate_library()

4. More information

For more details on the Imatest IT Python library, please see the instructions page on our website.

http://www.imatest.com/docs/it_python_instructions/
