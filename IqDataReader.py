import numpy as np
from sys import getsizeof as sizeof

class IqDataReader:
    def __init__(self, filename, minReadSize = 10000):
        self.__IQstream = open(filename)    

        #get file size
        self.__IQstream.seek(0,2)
        self.__fileSize = self.__IQstream.tell()
        self.__IQstream.seek(0,0)

        self.__loadedData = []

        self.__minReadSize = minReadSize
        self.__lastReadSize = 0
        self.__totalConsumedSize = 0
        self.__readIndexSize = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self.eof():
            raise StopIteration

        if self.__readIndexSize >= len(self.__loadedData):
           self.__loadedData += list(np.fromfile(self.__IQstream, dtype=np.complex64, count=self.__minReadSize))

        returnVal = self.__loadedData[self.__readIndexSize]
        self.__readIndexSize+=1
        return returnVal

    def read(self, read_block_size=None, immediateConsume=True):
        self.consume(self.__readIndexSize)

        if self.eof():
            raise IndexError
        
        if read_block_size == None:
            read_block_size = int(self.getTotalSize())

        while len(self.__loadedData) < read_block_size:
            self.__loadedData += list(np.fromfile(self.__IQstream, dtype=np.complex64, count=max(read_block_size, self.__minReadSize)))

        returnData = self.__loadedData[:read_block_size]
        self.__lastReadSize = read_block_size
        
        #if immediateConsume is true this read will consume immediately
        if immediateConsume:
            self.consume()

        return returnData

    def consume(self, *arg):
        if len(arg) > 0:
            consumedSize = arg[0]
        else:
            consumedSize = self.__lastReadSize
        consumedSize = min(len(self.__loadedData), consumedSize)
        self.__loadedData = self.__loadedData[consumedSize:]
        self.__totalConsumedSize += consumedSize
        self.__readIndexSize = 0
        return self.__totalConsumedSize
        
    def getTotalSize(self):
        return self.getTotalByteSize()/8

    def getTotalByteSize(self):
        return self.__fileSize

    def getConsumedByteSize(self):
        return self.__IQstream.tell()

    def getConsumedSize(self):
        return self.__totalConsumedSize + self.__readIndexSize

    def getRemainSize(self):
        return self.getRemainByteSize()/8

    def getRemainByteSize(self):
        return self.__fileSize - self.__IQstream.tell()

    def eof(self):
        if self.getRemainByteSize()<=0:
            return True
        else:
            return False
