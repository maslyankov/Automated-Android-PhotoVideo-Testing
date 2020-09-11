# Python 3 code to rename multiple
# files in a directory or folder's subdirectories
# Script uses arguments files located at each subdir - suffixes.txt
# Arg files should contain suffixes seperated by new line
# First line of arg files - "cases" will rename images with caseN name base, otherwise if for ex first line is "gosho" will rename files to gosho_...
# Second line (argument) specifies if we should start parsing files in ASCending (asc) or DESCending order (desc).

# importing modules
import os, glob, sys

# Globals
cases_cont_from = 0
files_last_list_len = 0

# Sorting Functions
def find_first_digit(s, non=False):
    for i, x in enumerate(s):
        if x.isdigit() ^ non:
            return i
    return -1

def split_digits(s, case=False):
    non = True
    while s:
        i = find_first_digit(s, non)
        if i == 0:
            non = not non
        elif i == -1:
            yield int(s) if s.isdigit() else s if case else s.lower()
            s = ''
        else:
            x, s = s[:i], s[i:]
            yield int(x) if x.isdigit() else x if case else x.lower()

def natural_key(s, *args, **kwargs):
    return tuple(split_digits(s, *args, **kwargs))

# Function to rename multiple files
def rename_files_in_dir(basepath, beg_with, ext):
    global cases_cont_from, files_last_list_len

    basepath += os.path.sep

    print("Basepath is: " + basepath)
    print("arg0 is: " + sys.argv[0])

    i = 1
    while os.path.exists("case%s.mp4" % i):
        i += 1
    cases_cont_from = i - 1

    print("Cont from: " + str(cases_cont_from))

    #for handler in get_logs.root.handlers[:]:
    #    get_logs.root.removeHandler(handler)

    logfile = basepath + 'renaming.log'  # TODO - Add folder name to log file name
    print("Log File:" + logfile)
    #get_logs.basicConfig(filename=logfile, level=get_logs.DEBUG, format='%(asctime)s %(message)s')

    #get_logs.info('-----------------------------')
    #get_logs.info('Log started!')

    #get_logs.info('Starting at dir: ' + basepath + "\n")

    files_list = sorted(glob.glob(basepath + beg_with + '*.' + ext), key=natural_key, reverse=False)
    #get_logs.info("Files List: \n" + str(files_list) + "\n")

    files_count = len(files_list)
    files_last_list_len = files_count

    if files_count == 0:
        print("No new files found! Terminating...")
        #get_logs.info("No new files found! Terminating...")
        return

    print("Beginning renaming in " + basepath + "\n")
    #get_logs.info("Beginning renaming in " + basepath + "\n")

    # Iterate through the files in the dir
    for count, filename in enumerate(files_list):
        prefix = "case" + str(cases_cont_from + count + 1)

        dst = basepath + prefix + "." + ext
        src = filename

        # rename() function will
        # try to rename all the files one by one
        try:
            os.rename(src, dst)
            #get_logs.info("Renaming file: " + src + " -> " + dst)
        except OSError:
            print("Files with those names already exist! Aborting!")
            #get_logs.error("Files with those names already exist! Aborting!\n")
            return
    #get_logs.info("Done with this folder.\n")

