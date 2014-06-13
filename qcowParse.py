#https://github.com/qemu/QEMU/blob/master/docs/specs/qcow2.txt
#http://forge.univention.org/bugzilla/attachment.cgi?id=3426
#https://docs.python.org/2.7/library/struct.html#format-strings

import struct
import sys
import os
import argparse #for parsing of argumenets

def createParser ():
	parser = argparse.ArgumentParser()
	parser.add_argument ('-d', '--directory', default = 'img')
	parser.add_argument ('-f', '--file', default = 'cir.img')

	return parser


#f = open ('img/Fedora-x86_64-19-20140407-sda.qcow2', 'rb')
cirpath = 'img/cir.img'
fedpath = 'img/fed.qcow2'
diskpath = 'img/disk.img'
sspath = 'img/ss.img'

parser = createParser()
namespace = parser.parse_args(sys.argv[1:])

currentpath = format(namespace.directory + '/' + namespace.file)

f = open (currentpath, 'rb')

def getInfo (file, begin, read, paramOfUnpack):
	file.seek(begin)
	info_ = file.read(read)
	info = struct.unpack(paramOfUnpack, info_)
	return 	str(info[0])

def getBFName (file, backing_file_offset_start, backing_file_size):
	if (int(backing_file_offset_start)==0):
		return 'There is not any backing file found'
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
	ss_name  =struct.unpack(str(len_name[0])+'s', ss_name_)
	currentlength = int(int(ss_offset)+40+int(ex_data_size[0])+len_id[0]+len_name[0])#offset to padding to round up
	while (currentlength%8!=0):
		currentlength+=1
	ssobj = {'ss_id': ss_id[0], 'ss_name':ss_name[0], 'ss_size':ss_size[0] , 'curlen':currentlength}
	return ssobj

def Print():
	nb_ss = getInfo(f, 60, 4, '>I') #number of snapshots
	ss_offset = getInfo(f, 64, 8, '>Q')
	print 'Filename: ' + str(os.path.abspath(currentpath))
	print 'Backing File path: ' + getBFName(f, getInfo(f, 8, 8, '>Q'), getInfo(f, 16, 4, '>I'))
	print 'Virtual Size (byte): ' + getInfo (f, 24, 8, '>Q')  #vsize
	print 'Size (byte): ' + str(os.stat(currentpath).st_size) #size
	print 'Snapshots offset: ' + getInfo(f, 64, 8, '>Q')
	for x in range(1, int(nb_ss)+1):
		ss = getSnapshot(f, ss_offset)
		print '-- Snapshot ID: ' + str(ss['ss_id'])
		print '-- Snapshot Name: ' + str(ss['ss_name'])
		print '-- Snapshot Size: ' + str(ss['ss_size'])
		ss_offset = ss['curlen']

def Main():
	backing_file_offset_start = getInfo(f, 8,8,'>Q') # trying to get BF offset. It returns '0' if isn't found
	ss_offset = getInfo(f, 64, 8, '>Q')

	Print()
Main()
#print 'size (byte): ' + str(os.stat("img/Fedora-x86_64-19-20140407-sda.qcow2").st_size)

f.close()