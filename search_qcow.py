##!/usr/bin/python
# Filename: search_qcow.py

import file_info
import os
import sys

def parse_dirs(src, dirs=0, files=0, qfi_files=0, files_data=None):
    """ returns array of qcow files-data
        and counts total files, dirs and qcow files
        Method walk through directory and searchs qcow files

    """
    if files_data is None:
        files_data = []

    for each_file in os.listdir(src): #for each file in current folder
        file_wp = os.path.join(src, each_file) #full path to file (with folders)
        if os.path.isdir(file_wp): #if file_wp is folder
            dirs += 1
            sys.stdout.write('\nFolder: ' + file_wp)
            files_data, dirs, files, qfi_files = \
                parse_dirs(file_wp, dirs, files, qfi_files, files_data)
        elif os.stat(file_wp).st_size != 0:
            file_o = open(file_wp, 'rb') #opened file
            files += 1
            sys.stdout.write("\nFile: " + file_wp)
            if file_info.get_info(file_o, 0, 3, '3s') == 'QFI':
                qfi_files += 1
                sys.stdout.write(' - QFI-file')
                dict_of_file_data = file_info.get_file_dict(file_o)
                files_data.append(dict_of_file_data)
            file_o.close()
        else:
            files += 1
            sys.stdout.write("\nFile: " + file_wp + " - EMPTY-file")

    return files_data, dirs, files, qfi_files


# End of search_qcow.py   