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

import struct
import sys
import os
import argparse #for parsing of argumenets
import json
from collections import OrderedDict  #for sorting keys in dictionary


class MyError(Exception):
    """My own Exception class"""
    pass

def create_parser():
    """Function creates parser of params"""
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--directory', default='img')
    parser.add_argument('-f', '--file', default='test.json')

    return parser

PARSER = create_parser()
NAMESPACE = PARSER.parse_args(sys.argv[1:])
CURRENTPATH = format(NAMESPACE.directory)
OS = sys.platform #operation system

try:
    if not os.path.exists(CURRENTPATH):
        raise MyError('The path ("{0}") does not exist. \n'.format(CURRENTPATH))
except MyError as err:
    sys.stdout.write(err.message)
    exit(0)

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
            if get_info(file_o, 0, 3, '3s') == 'QFI':
                qfi_files += 1
                sys.stdout.write(' - QFI-file')
                dict_of_file_data = get_file_dict(file_o)
                files_data.append(dict_of_file_data)
            file_o.close()
        else:
            files += 1
            sys.stdout.write("\nFile: " + file_wp + " - EMPTY-file")

    return files_data, dirs, files, qfi_files

def get_info(curf, begin, read, param_of_unpack):
    """ Method read 'read' bytes of current file 'curf' from 'begin'-byte,
     unpack them with 'param_of_unpack'
    """
    curf.seek(begin)
    info = curf.read(read)
    info = struct.unpack(param_of_unpack, info)
    return  str(info[0])

def get_bf_name(qcowf, backing_file_offset_start, backing_file_size):
    """ Method returns backing file name """
    if int(backing_file_offset_start) == 0:
        return -1 #if backing missed
    else:
        int_bf_offset = int(backing_file_offset_start)
        int_bf_size = int(backing_file_size)

        qcowf.seek(int_bf_offset)
        info = qcowf.read(int_bf_size)  #read all backing file bytes
        info = struct.unpack(str(int_bf_size)+'s', info)  #unpack bf info
        return str(info[0])

def get_shapshot_info(qcowf, ss_offset):
    """Method returns dictionary with information about snapshot """
    #file_.seek(int(ss_offset)+12)#length of id
    qcowf.seek(int(ss_offset)+12)#length of id
    len_id = qcowf.read(2)
    len_id = struct.unpack('>H', len_id)

    qcowf.seek(int(ss_offset)+14)#length of name
    len_name = qcowf.read(2)
    len_name = struct.unpack('>H', len_name)

    qcowf.seek(int(ss_offset)+32)# size of ss
    ss_size = qcowf.read(4)
    ss_size = struct.unpack('>I', ss_size)

    qcowf.seek(int(ss_offset)+36)#size of extra data
    ex_data_size = qcowf.read(4)
    ex_data_size = struct.unpack('>I', ex_data_size)

    #offset to id position
    qcowf.seek(int(int(ss_offset)+40+int(ex_data_size[0])))
    ss_id = qcowf.read(int(len_id[0]))
    ss_id = struct.unpack('c', ss_id)

    #offset to name position
    qcowf.seek(int(int(ss_offset)+40+int(ex_data_size[0])+len_id[0]))
    ss_name = qcowf.read(int(len_name[0]))
    ss_name = struct.unpack(str(len_name[0])+'s', ss_name)

    #offset to padding to round up
    currentlength = \
        int(int(ss_offset)+40+int(ex_data_size[0])+len_id[0]+len_name[0])

    while currentlength % 8 != 0:
        currentlength += 1

    ssobj = {'id': ss_id[0], 'name':ss_name[0], 'virtual_size':ss_size[0]}

    return (ssobj, currentlength) #sorted snapshot info + its length

def get_file_dict(qcowf):
    """ Method returns dictionary with information about file """
    qcow_dict = {} #create dictionary of file info

    nb_ss = int(get_info(qcowf, 60, 4, '>I')) #number of snapshots
    ss_offset = get_info(qcowf, 64, 8, '>Q')  #snapshots offset
    filename = str(os.path.abspath(qcowf.name))
    size = str(os.stat(qcowf.name).st_size)
    virtual_size = get_info(qcowf, 24, 8, '>Q')
    backing_file = get_bf_name(
        qcowf, get_info(qcowf, 8, 8, '>Q'), get_info(qcowf, 16, 4, '>I'))

    if OS == 'win32':
        filename = filename.replace('\\', '/') #correct view of path to files

    qcow_dict['filename'] = filename
    qcow_dict['size'] = size
    qcow_dict['virtual_size'] = virtual_size

    if backing_file != -1:
        qcow_dict['backing_file'] = backing_file

    if nb_ss != 0: #if there are any snapshots in file
        qcow_dict['snapshots'] = []
        keyorder_ss = ["id", "name", "virtual_size"]
        for _ in range(1, nb_ss+1): #go through all snapshots
            ss_dict, ss_offset = get_shapshot_info(qcowf, ss_offset)
            #keyorder_ss = ["id", "name", "virtual_size"]
            ss_dict_sorted = OrderedDict(sorted(ss_dict.items(), \
                key=lambda i: keyorder_ss.index(i[0])))
            qcow_dict['snapshots'].append(ss_dict_sorted)

    #keyorder_file = ["filename", "size", \
    #"virtual_size", "backing_file", "snapshots"]
    #qcow_dict = OrderedDict(sorted(qcow_dict.items(), \
    #    key=lambda i: keyorder_file.index(i[0])))
    return qcow_dict

#array of files in dict-format, quantity of dirs, files checked and qfi files
FILES, Q_DIRS, Q_FILES, QFI_FILES = parse_dirs(CURRENTPATH)
try:
    if Q_FILES == 0:
        raise MyError("There are no any files in folder ('{0}').\n"\
            .format(CURRENTPATH))
except MyError as err: #if error catched
    sys.stdout.write(err.message)
    exit(0)
else: #if there are no any exceptions
    with open(NAMESPACE.file, 'w') as outfile:
        #indent - friendly view in json, ensure_ascii - russian letters in path
        json.dump(FILES, outfile, indent=2, ensure_ascii=False)
    #folders, include current
    sys.stdout.write(\
        '\n\nFoldes: {0}, files: {1}, Qcow-files: {2}.\n'\
        .format(Q_DIRS, Q_FILES, QFI_FILES))




