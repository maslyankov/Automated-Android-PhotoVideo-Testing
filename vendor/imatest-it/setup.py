# Copyright 2015 The MathWorks, Inc.

from distutils.core import setup
from distutils.command.clean import clean
from distutils.command.install import install
import os
import glob
import platform

class InstallRuntime(install):
    # Calls the default run command, then deletes the build area 
    # (equivalent to "setup clean --all").
    def run(self):
        install.run(self)
        c = clean(self.distribution)
        c.all = True
        c.finalize_options()
        c.run()


if __name__ == '__main__':

    setup(
        name="imatest_it",
        version="2020.2.0",
        description='A module to call Imatest IT using Python',
        author='Imatest, LLC',
        author_email='support@imatest.com',
        url='http://www.imatest.com/docs/imatest-it-instructions/#Python',
        platforms=['Linux', 'Windows', 'MacOS'],
        packages=[
            'imatest',
            'imatest.library'
        ],
        package_data={'imatest.library': ['*.ctf']},
        # Executes the custom code above in order to delete the build area.
        cmdclass={'install': InstallRuntime},
    )

    install_dir = os.path.dirname(os.path.abspath(__file__))
    sample_dir = os.path.abspath(
        os.path.join(install_dir, os.path.pardir, os.path.pardir, os.path.pardir, 'samples', 'python'))
    if platform.system() == 'Windows':
        sample_dir = sample_dir.replace('\\', '\\\\')
    search_dir = os.path.join(sample_dir, '*', '*.ini')
    ini_files = glob.glob(search_dir)

    file_data = ''

    for ini_file in ini_files:
        with open(ini_file, 'r') as f_in:
            file_data = f_in.read()

        file_data = file_data.replace('{SAMPLE_DIR}', sample_dir)

        with open(ini_file, 'w') as f_out:
            f_out.write(file_data)
