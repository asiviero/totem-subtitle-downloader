import struct
import os
from gi.repository import Gio

SIZE_ERROR = -1
SEEK_ERROR = -2

def hashFile(name):
       """ FIXME Need to handle exceptions !! """

 
       longlongformat = 'q'  # long long 
       bytesize = struct.calcsize(longlongformat) 
           
       fp = Gio.File.new_for_uri (name)
           
       file_info = fp.query_info ('standard::size', 0, None)
       filesize = file_info.get_attribute_uint64 ('standard::size')
       
       hash = filesize 
          
       if filesize < 65536 * 2: 
              return SIZE_ERROR, 0

       data = file(fp.get_path(), 'rb')
       
       for x in range(65536/bytesize):
               buffer = data.read(bytesize)
               (l_value,)= struct.unpack(longlongformat, buffer)  
               hash += l_value 
               hash = hash & 0xFFFFFFFFFFFFFFFF #to remain as 64bit number  
               
       data.seek (max (0, filesize - 65536), os.SEEK_SET)

       if data.tell() != max (0, filesize - 65536):
               return SEEK_ERROR, 0

       for x in range(65536/bytesize):
               buffer = data.read(bytesize)
               (l_value,)= struct.unpack(longlongformat, buffer)  
               hash += l_value 
               hash = hash & 0xFFFFFFFFFFFFFFFF 
        
       data.close() 
       returnedhash =  "%016x" % hash 
       return returnedhash, filesize 

