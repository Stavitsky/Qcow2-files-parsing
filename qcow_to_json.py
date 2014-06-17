#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Qcow searcher

    This module searchs Qcow-files in specified directory
    and return them to specified file in JSON-format.


"""

#https://github.com/qemu/QEMU/blob/master/docs/specs/qcow2.txt
#http://forge.univention.org/bugzilla/attachment.cgi?id=3426
#https://docs.python.org/2.7/library/struct.html#format-strings
#https://docs.python.org/2/library/json.html

import search_qcow
import parsers
import sys
import json
import os

class MyError(Exception):
    """My own Exception class"""
    pass


def main():
    """ main function insert qcow files info to json outfile"""
    currentpath = parsers.currentpath # -d directory to search
    outfile = parsers.currentfile # -f output json file

    try:
        if not os.path.exists(currentpath):
            raise MyError('The path ("{0}") does not exist. \n'\
                .format(currentpath))
    except MyError as err:
        sys.stdout.write(err.message)
        exit(0)

    #array of files in dict-format, quantity of dirs, files checked and qfi
    files, q_dirs, q_files, qfi_files = search_qcow.parse_dirs(currentpath)

    try:
        if q_files == 0:
            raise MyError("There are no any files in folder ('{0}').\n"\
                .format(currentpath))
    except MyError as err: #if error catched
        sys.stdout.write(err.message)
        exit(0)
    else: #if there are no any exceptions
        with open(outfile, 'w') as outfile:
            #indent - friendly view in json, ensure-russian letters in path
            json.dump(files, outfile, indent=2, ensure_ascii=False)
        #folders, include current
        sys.stdout.write(\
            '\n\nFoldes: {0}, files: {1}, Qcow-files: {2}.\n'\
            .format(q_dirs, q_files, qfi_files))

if __name__ == '__main__':
    main()




