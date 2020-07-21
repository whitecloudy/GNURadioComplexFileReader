import numpy as np

class IqDataReader:
    def __init__(self, filename):
        self.__IQstream = open(filename)    

        #get file size
        self.__IQstream.seek(0,2)
        self.__fileSize = __IQstream.tell()
        self.__IQstream.seek(0,0)

    def read(self, read_block_size):
        return list(np.fromfile(self.__IQstream, dtype=np.complex64, count=read_block_size))

    def getTotalSize(self):
        return __fileSize

    def getConsumedSize(self):
        return __IQstream.tell()

    def getRemainSize(self):
        return __fileSize - __IQstream.tell()
