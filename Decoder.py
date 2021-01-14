from IqDataReader import IqDataReader as iqReader

class readerDecoder:
    readerStage = {4:"delimiter", 3:"data0", 2:"RTcal", 1:"TRcal", 0:"Data"}
    def __init__(self, sampleRate):
        self.sampleRate = sampleRate
        self.delimSample = int(12e-6 * self.sampleRate)
        self.PWSample = int(24e-6 * self.sampleRate)
        self.RTcalSample = self.PWSample * 6
        self.TRcalSample = int(8/40e3 * self.sampleRate)

        self.currentState = 4
        self.decodeBit = -1

    def resetAll(self):
        self.currentState = 4
        self.decodeBit = -1

    def downPulse(self, upSigLen):
        expected_len = 0

        if self.readerStage[self.currentState] is "delimiter":
            return self.readerStage[self.currentState], self.decodeBit
        elif self.readerStage[self.currentState] is "data0":
            expected_len = self.PWSample
        elif self.readerStage[self.currentState] is "RTcal":
            expected_len = self.RTcalSample - self.PWSample
        elif self.readerStage[self.currentState] is "TRcal":
            expected_len = self.TRcalSample - self.PWSample
        elif self.readerStage[self.currentState] is "Data":
            expected_len = self.PWSample

        if self.readerStage[self.currentState] is "Data":   #decode reader bit
            if (expected_len*0.8) < upSigLen and upSigLen < (expected_len*1.2):
                self.decodeBit = 0
            elif (expected_len*3*0.8) < upSigLen and upSigLen < (expected_len*3*1.2):
                self.decodeBit = 1
            else:   #decode failed
                self.resetAll()
                return self.downPulse(upSigLen)
        elif (expected_len*0.8) < upSigLen and upSigLen < (expected_len*1.2):
            pass
        else:   #decode Failed
            if self.readerStage[self.currentState] is "delimiter":
                self.resetAll()
                return self.readerStage[self.currentState], self.decodeBit
            else:
                self.resetAll()
                return self.downPulse(upSigLen)

        return self.readerStage[self.currentState], self.decodeBit


    def upPulse(self, downSigLen):
        expected_len = 0

        if self.readerStage[self.currentState] is "delimiter":
            expected_len = self.delimSample
        elif self.readerStage[self.currentState] is "data0":
            expected_len = self.PWSample
        elif self.readerStage[self.currentState] is "RTcal":
            expected_len = self.PWSample
        elif self.readerStage[self.currentState] is "TRcal":
            expected_len = self.PWSample
        elif self.readerStage[self.currentState] is "Data":
            expected_len = self.PWSample

        if (expected_len*0.8) < downSigLen and downSigLen < (expected_len*1.2): #handle preamble
            self.currentState = max(self.currentState - 1, 0)   #go to next stage
        else:
            self.resetAll()
            if self.readerStage[self.currentState] is "delimiter":
                return self.readerStage[self.currentState], self.decodeBit
            else:
                return self.upPulse(downSigLen)

        return self.readerStage[self.currentState], self.decodeBit
 
        


class SampleHandler:
    def __init__(self, iqFile):
        self.iq_file = iqFile
        self.dcIQ = complex(0,0)
        self.averagingRatio = 0.2
        self.thresholdRatio = 0.1

        bitwise_reverse = list(256)

        for bit in range(256):
            rev_bit = bit

            rev_bit = ((rev_bit << 4) & 0xf0) | ((rev_bit >> 4) & 0x0f)
            rev_bit = ((rev_bit << 2) & 0xcc) | ((rev_bit >> 2) & 0x33)
            rev_bit = ((rev_bit << 1) & 0xaa) | ((rev_bit >> 1) & 0x55)

            bitwise_reverse[bit] = rev_bit


    def bits2byte(self, bits):
        data = 0
        for bit in bits:
            data *= 2
            if bit == 1:
                data += 1

        return data



    def findReaderSignal(self, avgSigStrength = None):
        findFlag = False
        
        readSize = 100000
        UD_counter = 0
        UD_flag = 1
        decoder = readerDecoder(2e6)

        while not findFlag:
            samples = self.iq_file.read(readSize, False)
            iq_idx = 0
            decode_state = -1
            decode_bits = []
            decode_flag = False

            for sample in samples:
                iq_idx += 1
                sample = sample - self.dcIQ
                sampleAbs = abs(sample)

                if UD_flag == 1:
                    if avgSigStrength*self.thresholdRatio > sampleAbs:
                        decode_state, bit = decoder.downPulse(UD_counter)
                        UD_flag = 0
                        UD_counter = 0
                        continue

                    UD_counter += 1

                elif UD_flag == 0:
                    if avgSigStrength*(1 - self.thresholdRatio) < sampleAbs:
                        decode_state, bit = decoder.upPulse(UD_counter)
 
                        if decode_flag:
                            decode_bits.append(bit)
                            if len(decode_bits) >= 136:
                                self.iq_file.consume(iq_idx)
                                return decode_bits, avgSigStrength
                        elif decode_state == "Data":
                            decode_flag = True
                                                            
                        UD_flag = 1
                        UD_counter = 0
                        continue

                    UD_counter += 1

            self.iq_file.consume(readSize)

    def proc(self):
        samples = self.iq_file.read(20000)
        idx = 0

        for iq in samples:
            if idx >= 10000:
                break
            else:
                idx += 1
            self.dcIQ += iq

        self.dcIQ /= 10000

        samples = self.iq_file.read(1000)
        avgIQ = complex(0.0,0.0)

        for iq in samples:
            avgIQ += (iq - self.dcIQ)

        avgIQ /= 1000

        for i in range(4000):
            data, avgSignal = self.findReaderSignal(abs(avgIQ))
            for j in range(1, 17):
                byte = data[j*8:j*8 + 8]
                print(self.bits2byte(byte))

            

def main():
    iqfile = iqReader("data/1_1")
    handler = SampleHandler(iqfile)
    handler.proc()


if __name__=='__main__':
    main()
