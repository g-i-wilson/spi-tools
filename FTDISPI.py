from pyftdi.spi import SpiController
from pyftdi.gpio import GpioSyncController
import serial
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

class bcolors:
    WHITE = '\033[37m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    RED = '\033[31m'
    RESET = '\033[0m'

def printByte(a, b):
    for bit in range(8):
        a_bit = (a >> (7-bit)) & 0x01
        b_bit = (b >> (7-bit)) & 0x01
        if a_bit and b_bit:
            print("1", end='')
        elif (not a_bit) and b_bit:
            print(bcolors.GREEN, end='')
            print("1", end='')
        elif a_bit and (not b_bit):
            print(bcolors.RED, end='')
            print("0", end='')
        else:
            print("0", end='')
        print(bcolors.RESET, end='')
    print(end='  ')

def printReg(addrName, addr=[], data=[], old_data=None, note="", nameColWidth=18):
    print( addrName+(" "*(nameColWidth-len(addrName))), end=' ')
    for a in addr:
        if old_data:
            print(bcolors.GREEN, end='')
            print("0x{:02x}".format(a), end=' ')
            print(bcolors.RESET, end='')
        else:
            print("0x{:02x}".format(a), end=' ')
    print('  |  ', end='')
    for i in range(len(data)):
        print("0x{:02x}".format(data[i]), end=' ')
        if old_data:
            printByte(old_data[i], data[i])
        else:
            printByte(data[i], data[i])
    print('  |  '+note)

def printStruct(struct):
    for name in struct:
        if 'old_data' in struct[name]:
            printReg(name, addr=struct[name]['addr_w'], data=struct[name]['data'], old_data=struct[name]['old_data'], note=struct[name]['info'])
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




class GPIO:
    def __init__(self, gpio, SCLK=0x10, MOSI=0x20, MISO=0x40, CS=0x80):
        self.gpio = gpio
        self.SCLK = SCLK
        self.MOSI = MOSI
        self.MISO = MISO
        self.CS = CS
        self.txList = []
        self.readFlag = []
        self.rxList = []
    def transaction(self, byteList, readSize=0): # readSize 0 is simply a write
        self.txList = [self.CS] # CS high, others low
        self.readFlag = []
        self.insertDelay(4)
        self.clockLow()
        self.csLow()
        for aByte in byteList:
            self.writeByte(aByte)
            self.readFlag.append(False)
        for i in range(readSize):
            self.writeByte(0x00)
            self.readFlag.append(True)
        self.csHigh()
        self.clockLow()
        self.insertDelay(4)
        self.transmit()
    def insertDelay(self, d):
        for i in range(d):
            self.txList.append(self.txList[-1])
    def clockLow(self):
        self.txList.append( self.txList[-1] & ~self.SCLK )
    def clockLowdataHigh(self):
        self.txList.append( (self.txList[-1] & ~self.SCLK) | self.MOSI )
    def clockLowdataLow(self):
        self.txList.append( (self.txList[-1] & ~self.SCLK) & ~self.MOSI )
    def clockHigh(self):
        self.txList.append( self.txList[-1] | self.SCLK )
    def csLow(self):
        self.txList.append( self.txList[-1] & ~self.CS )
    def csHigh(self):
        self.txList.append( self.txList[-1] | self.CS )
    def writeByte(self, aByte):
        for i in range(8):
            shiftPlaces = 7-i # MSB first "big endian"
            # clock falling edge and data transition
            if ((aByte >> shiftPlaces) & 0x01):
                self.clockLowdataHigh()
            else:
                self.clockLowdataLow()
            # clock rising edge
            self.clockHigh()
    def readByte(self):
        self.writeByte(0x00, read=True)
    def getTxList(self):
        return self.txList
    def transmit(self):
        rxBytes = self.gpio.exchange( self.txList );
        self.rxList = []
        for byte in rxBytes:
            self.rxList.append(byte)
    def getRxList(self):
        return self.rxList
    def getReadFlag(self):
        return self.readFlag
    def read(self, byteList, readSize):
        self.transaction(byteList, readSize)
        rxByteList = self.readBitBang()
        rxByteListOut = []
        for i in range(len(self.readFlag)):
            if self.readFlag[i]:
                rxByteListOut.append(rxByteList[1][i])
        return rxByteListOut
    def write(self, byteList):
        self.transaction(byteList)
    def readBitBang(self):
        mosiArray = []
        misoArray = []
        bitPlace = 7
        mosiByte = 0x00
        misoByte = 0x00
        for a in range(len(self.rxList)):
            if (not (self.rxList[a-1] & self.SCLK) and (self.rxList[a] & self.SCLK)): # rising edge
                if (self.rxList[a] & self.MOSI):
                    mosiByte += (1 << bitPlace)
                if (self.rxList[a] & self.MISO): # data=1
                    misoByte += (1 << bitPlace)
                bitPlace -= 1
            if bitPlace < 0:
                mosiArray.append(mosiByte)
                misoArray.append(misoByte)
                mosiByte = 0x00
                misoByte = 0x00
                bitPlace = 7
        if dbg:
            print("MOSI: ")
            print(mosiArray)
            print("MISO: ")
            print(misoArray)
        return [mosiArray, misoArray]


class MPSSE:
    def __init__(self, slave):
        self.slave = slave
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
        byteArray = self.slave.exchange( \
            out=byteList, \
            readlen=readSize, \
            start=True, \
            stop=True, \
            duplex=False, \
            droptail=0 \
        )
        byteList = []
        for byte in byteArray:
            byteList.append(byte)
        return byteList


def blockUntilTrue(something):
    while(1):
        if something:
            return

class UARTSPIBridge:
    def __init__(self, port="/dev/ttyUSB0", baudrate="9600"):
        self.serial = serial.Serial(port=port,baudrate=baudrate)
        if self.serial.is_open:
            self.serial.close()
        self.serial.open()
        self.serial.flush()
    def read(self, byteList, readLen):
        # send write-length byte, read-length byte, and first data byte
        self.serial.write( [ len(byteList), readLen ] );
        if len(byteList) > 0:
            self.serial.write( [ byteList[0] ] )
        self.serial.write( [ 0x0A ] ) # newline char
        self.serial.flush()
        time.sleep(0.1)
        # read acknowledgement bytes
        lenBytes = []
        # blockUntilTrue(self.serial.inWaiting())
        lenBytes.append( self.serial.read(1) )
        print("hi1")
        print(lenBytes)
        time.sleep(0.1)
        # blockUntilTrue(self.serial.inWaiting())
        lenBytes.append( self.serial.read(1) )
        print("hi2")
        print(lenBytes)
        if lenBytes[0] != len(byteList).to_bytes(1,'big') or lenBytes[1] != readLen.to_bytes(1,'big'):
            print("Error communicating with UARTSPIBridge")
            print("W length received: "+str(lenBytes[0])+" != "+str(byteList[0].to_bytes(1,'big')))
            print("R length received: "+str(lenBytes[1])+" != "+str(byteList[1].to_bytes(1,'big')))
            #return []
        time.sleep(0.1)
        # blockUntilTrue(self.serial.inWaiting())
        print("hi3")
        self.serial.read(1) # ack byte from first data-write byte
        # write the remainder of byteList
        for i in range(1,len(byteList)):
            self.serial.write(outByte[i])
            self.serial.write( 0x0A ) # newline char
            self.serial.flush()
            blockUntilTrue(self.serial.inWaiting())
            self.serial.read(1) # ack byte for each data-write byte
        inList = []
        for i in range(readLen):
            blockUntilTrue(self.serial.inWaiting())
            inList.append( self.serial.read(1) )
        return inList
    def write(self, byteList):
        return self.read(byteList, 0);


class Interface:

    def __init__(self, rwObject, defaultMap, currentState, previousState):
        self.rwObject = rwObject
        # default register map
        defaultMapFile = JSONFile.load(defaultMap)
        if not defaultMapFile.fileExists():
            print("Unable to load "+defaultMap)
            exit()
        self.defaultMap = defaultMapFile.read()
        # states for comparison
        self.previousState = JSONFile.load(previousState)
        if not self.previousState.fileExists():
            print("Unable to load "+currentState)
            exit()
        self.currentState = JSONFile.load(currentState)
        if not self.currentState.fileExists():
            print("Unable to load "+currentState)
            exit()


    def fillDefaults(self, struct={}):
        for name in struct:
            if name in self.defaultMap.keys():
                for key in self.defaultMap[name].keys():
                    if not key in struct[name].keys():
                        struct[name][key] = self.defaultMap[name][key]

    def writeStruct(self, struct, display=False):
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
                            print("Write: "+pre_name+", "+printByteList( createByteList(self.defaultMap[pre_name]['addr_w'], step[pre_name]) ))
                        self.rwObject.write( createByteList(self.defaultMap[pre_name]['addr_w'], step[pre_name]) )
            if dbg:
                print("Write: "+name+", "+printByteList(createByteList(struct[name]['addr_w'], struct[name]['data'])))
            self.rwObject.write( createByteList(struct[name]['addr_w'], struct[name]['data']) )
        if display:
            printStruct(struct)
        return struct

    def readStruct(self, struct, display=False):
        self.fillDefaults(struct)
        for name in struct:
            if 'pre_r' in struct[name]:
                for step in struct[name]['pre_r']: # ...is a list
                    for pre_name in step: # step is a dictionary with one key
                        if dbg:
                            print("Write: "+pre_name+", "+printByteList( createByteList(self.defaultMap[pre_name]['addr_w'], step[pre_name]) ))
                        self.rwObject.write( createByteList(self.defaultMap[pre_name]['addr_w'], step[pre_name]) )
            struct[name]['data'] = self.rwObject.read( struct[name]['addr_r'], len(struct[name]['data']) )
            if dbg:
                print("Read: "+name+", "+printByteList(createByteList(struct[name]['addr_r'], struct[name]['data'])))
        if display:
            printStruct(struct)
        return struct

    def readState(self, display=True):
        self.previousState.write(self.currentState.read())
        struct = {}
        for name in self.defaultMap:
            struct[name] = {}
        self.currentState.write(self.readStruct(struct, display))
        return self.currentState.read()

    def compare(self, display=True, pre_display="", post_display=""):
        self.readState(display=False)
        comparison = {}
        if len(self.previousState.read().keys()) == 0:
             self.readState(display=False)
        for name in self.currentState.read():
            # aliases
            prevData = self.previousState.read()[name]['data']
            currData = self.currentState.read()[name]['data']
            same = True
            for i in range(len(currData)):
                if currData[i] != prevData[i]:
                    same = False
            if not same:
                comparison[name] = {}
                comparison[name]['data'] = currData
                comparison[name]['old_data'] = prevData
                self.fillDefaults(comparison)
        if display and len(comparison.keys()) > 0:
            if pre_display:
                print(pre_display)
            printStruct(comparison)
            if post_display:
                print(post_display)
        return comparison

    def trigger(self, display=True, pre_display="", delay=.25):
        while(1):
            comp = self.compare(display=False)
            if len(comp.keys()) > 0:
                if display:
                    print(pre_display)
                    printStruct(comp)
                return comp
            time.sleep(delay)

    def writeDefault(self, display=True):
        struct = self.writeStruct(self.defaultMap)
        return self.readState(display)

    def writeBits(self, name, bitStrings=[], display=True, compare=True):
        if compare:
            self.compare(display=display, pre_display="Changes before write:")
        if display:
            print("Writing...")
        struct = self.writeStruct( { name : bitMaskToBytes(bitStrings) }, display )
        if compare:
            self.currentState.merge(struct) # also merges everything into struct
            self.compare(display=display, pre_display="Changes after write:")
        return {name: struct[name]} # return only this name

    def writeBitsList(self, bitsList):
        for bits in bitsList:
            self.writeBits(name=bits[0], bitStrings=bits[1])






def ui_hex(str):
    return int(str,16)

def uiLoopHelp():
    print()
    print("Command set:")
    print()
    print("write <REG_NAME> XXXX1010 1XXXXXX0       | Write bits (any char not 0 or 1 is a don't-care)")
    print("read <REG_NAME>                          | Read register")
    print("all                                      | Read all registers")
    print("save <fileName>                          | Save registers to JSON file")
    print("load <fileName>                          | Load and write registers from JSON file")
    print("loadDefault                              | Load datasheet default JSON configuration")
    print("help                                     | Print this command set")
    print("exit                                     | Exit the program")

def uiLoop(spiObject, printHelp=True):
    if printHelp:
        uiLoopHelp()
    jsonObject = None
    ui = [""]
    while (ui[0] != "exit"):
        print("\n> ", end='')
        ui = sys.stdin.readline().rstrip().split(' ')

        if (ui[0] == "read"):
            spiObject.readStruct({ ui[1] : {} }, display=True)
        if (ui[0] == "write"):
            dataRegs = []
            for i in range(2,len(ui)):
                dataRegs.append( ui[i] )
            spiObject.writeBits( ui[1], dataRegs )
        if (ui[0] == "all"):
            spiObject.readState()
        if (ui[0] == "compare"):
            spiObject.compare()
        if (ui[0] == "trigger"):
            while(1):
                spiObject.trigger(pre_display=chr(27)+"[2J")
                time.sleep(1)
        if (ui[0] == "save"):
            if jsonObject is None:
                if len(ui) > 1:
                    jsonObject = JSONFile.new(ui[1])
                else:
                    jsonObject = JSONFile.new(input("\nSave as: "))
            jsonObject.write( spiObject.readState() )
        if (ui[0] == "load"):
            if jsonObject is None:
                jsonObject = JSONFile.load(ui[1])
            spiObject.writeStruct(jsonObject.read())
            spiObject.readState()
        if (ui[0] == "loadDefault"):
            spiObject.writeDefault()
        if (ui[0] == "help"):
            uiLoopHelp()
