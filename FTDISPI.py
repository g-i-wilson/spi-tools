from pyftdi.spi import SpiController
import time
import sys
import JSONFile

dbg = False

def createByteList(addrList, dataList):
    newBytes = []
    for byte in addrList:
        newBytes.append(byte)
    for byte in dataList:
        newBytes.append(byte)
    return newBytes

def printByteList(byteList):
    str = ""
    for byte in byteList:
        str += hex(byte)+" "
    return str

def readModifyWrite(old=[], mask=[], new=[]):
    for i in range(len(old)):
        new[i] = (old[i] & ~mask[i]) | new[i]

def printByte(aByte):
    for aBit in range(8):
        if ((aByte >> (7-aBit)) & 0x01):
            print("1 ", end='')
        else:
            print("_ ", end='')

def printReg(addrName, addr=[], data=[], note="", nameColWidth=18):
    print( addrName+(" "*(nameColWidth-len(addrName))), end=' ')
    for a in addr:
        print("0x{:02x}".format(a), end=' ')
    print('  |  ', end='')
    for d in data:
        print("0x{:02x}".format(d), end=' ')
        printByte(d)
    print('  |  '+note)

def printStruct(struct):
    for name in struct:
        if 'old_data' in struct[name]:
            printReg(name, addr=struct[name]['addr_w'], data=struct[name]['old_data'], note=struct[name]['info'])
            printReg("--> "+name, addr=struct[name]['addr_w'], data=struct[name]['data'], note=struct[name]['info'])
        else:
            printReg(name, addr=struct[name]['addr_w'], data=struct[name]['data'], note=struct[name]['info'])

def bitMaskToBytes(bitStrArray):
    data = []
    mask = []
    for bitStr in bitStrArray:
        bit = 0x80
        bitMask = 0x00
        bitData = 0x00
        for aChar in bitStr:
            if aChar == '1' or aChar == '0':
                bitMask += bit
            if aChar == '1':
                bitData += bit
            bit = bit >> 1
        data.append(bitData)
        mask.append(bitMask)
    return {"data":data, "mask":mask}




class Device:

    def __init__(self, ftdiDevice='ftdi:///2', defaultMap='default.json', cs=0, freq=1E6, mode=0):
        # SPI controller object
        self.spi = SpiController()
        self.spi.configure(ftdiDevice)
        self.slave = self.spi.get_port(cs, freq, mode)
        # default register map
        self.defaultMap = JSONFile.load(defaultMap).read()

    def write(self, byteList):
        self.slave.exchange( \
            out=byteList, \
            readlen=0, \
            start=True, \
            stop=True, \
            duplex=False, \
            droptail=0 \
        )

    def read(self, byteList, readSize):
        return self.slave.exchange( \
            out=byteList, \
            readlen=readSize, \
            start=True, \
            stop=True, \
            duplex=False, \
            droptail=0 \
        )

    def fillDefaults(self, struct={}):
        for name in struct:
            if name in self.defaultMap.keys():
                for key in self.defaultMap[name].keys():
                    if not key in struct[name].keys():
                        struct[name][key] = self.defaultMap[name][key]

    def writeStruct(self, struct):
        self.fillDefaults(struct)
        for name in struct:
            if 'mask' in struct[name]:
                old = {name : {}}
                self.readStruct(old)
                struct[name]['old_data'] = old[name]['data']
                readModifyWrite(old=struct[name]['old_data'], mask=struct[name]['mask'], new=struct[name]['data'])
            if 'pre_w' in struct[name]:
                for step in struct[name]['pre_w']: # ...is a list
                    for pre_name in step: # step is a dictionary with one key
                        if dbg:
                            print("Write: "+pre_name+", "+printByteList(createByteList(struct[name]['addr_w'], step[pre_name])))
                        self.write( createByteList(self.defaultMap[pre_name]['addr_w'], step[pre_name]) )
            if dbg:
                print("Write: "+name+", "+printByteList(createByteList(struct[name]['addr_w'], struct[name]['data'])))
            self.write( createByteList(struct[name]['addr_w'], struct[name]['data']) )
        return struct

    def readStruct(self, struct):
        self.fillDefaults(struct)
        for name in struct:
            if 'pre_r' in struct[name]:
                for step in struct[name]['pre_r']: # ...is a list
                    for pre_name in step: # step is a dictionary with one key
                        if dbg:
                            print("Write: "+pre_name+", "+printByteList(createByteList(struct[name]['addr_w'], step[pre_name])))
                        self.write( createByteList(self.defaultMap[pre_name]['addr_w'], step[pre_name]) )
            struct[name]['data'] = self.read( struct[name]['addr_r'], len(struct[name]['data']) )
            if dbg:
                print("Read: "+name+", "+printByteList(createByteList(struct[name]['addr_r'], struct[name]['data'])))
        return struct

    def currentState(self, display=True):
        currentState = {}
        for name in self.defaultMap:
            currentState[name] = {}
        if display:
            printStruct(currentState)
        return self.readStruct(currentState)

    def writeDefault(self, display=True):
        struct = self.writeStruct(self.defaultMap)
        return self.currentState(display)

    def writeBits(self, name, bitStrings=[], display=True):
        struct = self.writeStruct( { name : bitMaskToBytes(bitStrings) } )
        if display:
            printStruct(struct)
        return struct

    def writeBitsList(self, bitsList):
        for bits in bitsList:
            self.writeBits(name=bits[0], bitStrings=bits[1])
