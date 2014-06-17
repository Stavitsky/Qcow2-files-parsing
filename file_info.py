##!/usr/bin/python
# Filename: file_info.py
import sys
import struct
import os
from collections import OrderedDict  #for sorting keys in dictionary

OS = sys.platform #operation system

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
            qcow_dict['snapshots'].append(ss_dict)

    return qcow_dict



# End of file_info.py    