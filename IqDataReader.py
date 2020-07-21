import numpy as np

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

    def read(self, read_block_size, immediateConsume=True):
        if self.eof():
            raise IndexError

        if len(self.__loadedData) < read_block_size:
            self.__loadedData += list(np.fromfile(self.__IQstream, dtype=np.complex64, count=max(read_block_size, self.__minReadSize)))
        self.__lastReadSize = read_block_size
        returnData = self.__loadedData[:read_block_size]

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
        return self.__totalConsumedSize
        
    def getTotalSize(self):
        return self.__fileSize

    def getConsumedSize(self):
        return self.__totalConsumedSize

    def getRemainSize(self):
        return self.__fileSize - self.__totalConsumedSize

    def eof(self):
        if self.getRemainSize()==0:
            return True
        else:
            return False
