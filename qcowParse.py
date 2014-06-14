#!/usr/bin/python
# -*- coding: utf-8 -*- 

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

def createParser ():
	parser = argparse.ArgumentParser()
	parser.add_argument ('-d', '--directory', default = 'img/ss.img')
	parser.add_argument ('-f', '--file', default = 'test.json')

	return parser


#f = open ('img/Fedora-x86_64-19-20140407-sda.qcow2', 'rb')
cirpath = 'img/cir.img'
fedpath = 'img/fed.qcow2'
diskpath = 'img/disk.img'
sspath = 'img/ss.img'



parser = createParser()
namespace = parser.parse_args(sys.argv[1:])

currentpath = format(namespace.directory)

def parseDirs(sSrc, iDirs=0, iFiles=0):
	filelsData = []
	for file in os.listdir(sSrc):
		file_wp= os.path.join(sSrc,file) #full path to file (with dir)
		file_o = open (file_wp, 'rb')
		#print file_wp, file
		if os.path.isdir(file_wp):
			iDirs+=1
			iDirs, iFiles = parseDirs(file_wp,iDirs,iFiles)
		else:
			iFiles += 1
			print file_wp
			if (getInfo (file_o, 0, 3, '3s') == 'QFI'):
				print ("Найден файл QFI!")
				dictionaryOfFileData = getFileDict(file_o)
				filelsData.append(dictionaryOfFileData)
			file_o.close()

	return filelsData

#f = open (currentpath, 'rb')

def getInfo (file, begin, read, paramOfUnpack):
	file.seek(begin)
	info_ = file.read(read)
	info = struct.unpack(paramOfUnpack, info_)
	return 	str(info[0])

def getBFName (file, backing_file_offset_start, backing_file_size):
	if (int(backing_file_offset_start)==0):
		return -1 #if backing missed
	else:
		intBFOffset = int (backing_file_offset_start)
		intBFSize = int (backing_file_size) 

		file.seek(intBFOffset)
		info_ = file.read(intBFSize) #read all backing file bytes
		info = struct.unpack(str(intBFSize)+'s', info_)
		return str(info[0])

def getSnapshot(file, ss_offset):

	file.seek(int(ss_offset)+12)#length of id
	len_id_ = file.read(2)
	len_id = struct.unpack('>H', len_id_)

	file.seek(int(ss_offset)+14)#length of name
	len_name_ = file.read(2)
	len_name = struct.unpack('>H', len_name_)

	file.seek(int(ss_offset)+32)# size of ss
	ss_size_ = file.read(4)
	ss_size = struct.unpack('>I', ss_size_)

	file.seek(int(ss_offset)+36)#size of extra data
	ex_data_size_ = file.read(4)
	ex_data_size = struct.unpack('>I', ex_data_size_)

	file.seek(int(int(ss_offset)+40+int(ex_data_size[0])))#offset to id position
	ss_id_ = file.read(int(len_id[0]))
	ss_id = struct.unpack('c', ss_id_)

	file.seek(int(int(ss_offset)+40+int(ex_data_size[0])+len_id[0]))#offset to name position
	ss_name_ = file.read(int(len_name[0]))
	ss_name  = struct.unpack(str(len_name[0])+'s', ss_name_)

	currentlength = int(int(ss_offset)+40+int(ex_data_size[0])+len_id[0]+len_name[0])#offset to padding to round up
	while (currentlength%8!=0):
		currentlength+=1

	ssobj = {'id': ss_id[0], 'name':ss_name[0], 'virtual_size':ss_size[0]}


	return (ssobj, currentlength) #sorted snapshot info

def getFileDict(file):

	qcowDict = {} #create dictionary of file info

	nb_ss = int(getInfo(file, 60, 4, '>I')) #number of snapshots
	ss_offset = getInfo(file, 64, 8, '>Q')	#snapshots offset

	#filename = str(os.path.abspath(currentpath))
	filename = str(os.path.abspath(file.name))
	#size = str(os.stat(currentpath).st_size)
	size = str(os.stat(file.name).st_size)
	virtual_size = getInfo (file, 24, 8, '>Q')
	backing_file = getBFName(file, getInfo(file, 8, 8, '>Q'), getInfo(file, 16, 4, '>I'))

	qcowDict ['filename'] = filename
	qcowDict ['size'] = size
	qcowDict ['virtual_size'] = virtual_size

	if (backing_file != -1):
		qcowDict ['backing_file'] = backing_file

	if (nb_ss != 0): #if there are any snapshots in file
		qcowDict ['snapshots'] = [] 
		for i in range (1, nb_ss+1): #go around all snapshots
			snapShotObj, ss_offset = getSnapshot(file, ss_offset)

			keyorder_ss = ["id", "name", "virtual_size"]
			snapShotObj_sorted = OrderedDict(sorted(snapShotObj.items(), key = lambda i:keyorder_ss.index(i[0]))) 

			qcowDict['snapshots'].append(snapShotObj_sorted)

	keyorder_file = ["filename", "size", "virtual_size", "backing_file", "snapshots"]
	qcowDict = OrderedDict(sorted(qcowDict.items(), key = lambda i:keyorder_file.index(i[0])))


	
	return qcowDict
	
files = parseDirs(currentpath) #array of files in dict-format


with open (namespace.file, 'w') as outfile:
	json.dump(files, outfile, indent = 2)	
 