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


class MyError(Exception):
	def __init__(self,text):
		MyError.txt = text
		

def createParser ():
	parser = argparse.ArgumentParser()
	parser.add_argument ('-d', '--directory', default = 'img')
	parser.add_argument ('-f', '--file', default = 'test.json')

	return parser

parser = createParser()
namespace = parser.parse_args(sys.argv[1:])

currentpath = format(namespace.directory)

oper_system = sys.platform #operation system 

try:
	if (os.path.exists(currentpath) != True):
		raise MyError('The path (%s) does not exist. \n' % currentpath)
except MyError:
	sys.stdout.write(MyError.txt)	
	exit(0)	
	
def parseDirs(sSrc, iDirs=0, iFiles=0, qfiQiles=0, filesData = []):
	for file in os.listdir(sSrc):
		file_wp= os.path.join(sSrc,file) #full path to file (with dir)
		if os.path.isdir(file_wp):
			iDirs += 1
			sys.stdout.write('\nFolder: ' + file_wp)
			filesData, iDirs, iFiles, qfiQiles = parseDirs(file_wp,iDirs,iFiles,qfiQiles,filesData)
		else:
			file_o = open (file_wp, 'rb')
			iFiles += 1
			sys.stdout.write ("\nFile: " + file_wp)
			if (getInfo (file_o, 0, 3, '3s') == 'QFI'):
				qfiQiles += 1
				sys.stdout.write(' - QFI-file!')
				dictionaryOfFileData = getFileDict(file_o)
				filesData.append(dictionaryOfFileData)
			file_o.close()

	return filesData, iDirs, iFiles, qfiQiles

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

	filename = str(os.path.abspath(file.name))
	size = str(os.stat(file.name).st_size)
	virtual_size = getInfo (file, 24, 8, '>Q')
	backing_file = getBFName(file, getInfo(file, 8, 8, '>Q'), getInfo(file, 16, 4, '>I'))

	if (oper_system == 'win32'):
		filename = filename.replace('\\', '/') #correct view of path to files

	qcowDict ['filename'] = filename
	qcowDict ['size'] = size
	qcowDict ['virtual_size'] = virtual_size

	if (backing_file != -1):
		qcowDict ['backing_file'] = backing_file

	if (nb_ss != 0): #if there are any snapshots in file
		qcowDict ['snapshots'] = [] 
		for i in range (1, nb_ss+1): #go through all snapshots
			snapShotObj, ss_offset = getSnapshot(file, ss_offset)

			keyorder_ss = ["id", "name", "virtual_size"]
			snapShotObj_sorted = OrderedDict(sorted(snapShotObj.items(), key = lambda i:keyorder_ss.index(i[0]))) 

			qcowDict['snapshots'].append(snapShotObj_sorted)

	keyorder_file = ["filename", "size", "virtual_size", "backing_file", "snapshots"]
	qcowDict = OrderedDict(sorted(qcowDict.items(), key = lambda i:keyorder_file.index(i[0])))
	
	return qcowDict
	
files, q_dirs, q_files, qfi_files = parseDirs(currentpath) #array of files in dict-format, quantity of dirs and files looked

try:
	if (q_files == 0):
		raise MyError ("There are no any files in folder (%s).\n" % currentpath)
except MyError: #if error catched
	sys.stdout.write(MyError.txt)	
	exit(0)
else: #if there are no any exceptions
	with open (namespace.file, 'w') as outfile:
		#indent - friendly view in json, ensure_ascii - russian letters in path
		json.dump(files, outfile, indent = 2, ensure_ascii = False)
	#folders, include current
	sys.stdout.write('\n\n%s folders cheched. Found: %s files total, %s of those match Qcow extension.\n' % (q_dirs+1, q_files, qfi_files))	



				
			




