#https://github.com/qemu/QEMU/blob/master/docs/specs/qcow2.txt
#http://forge.univention.org/bugzilla/attachment.cgi?id=3426
#https://docs.python.org/2.7/library/struct.html#format-strings

import struct
import os
#f = open ('img/Fedora-x86_64-19-20140407-sda.qcow2', 'rb')
f = open ('img/cirros-0.3.2-x86_64-disk.img', 'rb')

def getInfo (file, begin, read, paramOfUnpack):
	file.seek(begin)
	info_ = file.read(read)
	info = struct.unpack(paramOfUnpack, info_)
	return 	str(info[0])

print 'magic: ' + getInfo (f, 0, 4, '4s')  #magic
print 'version: ' + getInfo (f, 4, 4, '>I')  #version
print 'virtual size (byte): ' + getInfo (f, 24, 8, '>Q')  #size
print 'size (byte): ' + str(os.stat("img/cirros-0.3.2-x86_64-disk.img").st_size)
#print 'size (byte): ' + str(os.stat("img/Fedora-x86_64-19-20140407-sda.qcow2").st_size)

f.close()
