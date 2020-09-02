from pyftdi.spi import SpiController
import time
import sys
import JSONFile


class SpiConfig:
    def __init__(self, ftdiDevice='ftdi:///2', debugFlag=False):
        self.debugFlag = debugFlag
        # default DUC -- can be 1 or 2
        self.multiDUC = 1
        # Instantiate a SPI controller
        self.spi = SpiController()
        # Configure the first interface (IF/1) of the FTDI device as a SPI master
        self.spi.configure(ftdiDevice)
        # Get a port to a SPI slave w/ /CS on A*BUS3 and SPI mode 0 @ 12MHz
        self.slave = self.spi.get_port(cs=0, freq=1E6, mode=0)
        # "Shadow" register map -- tries to stay in sync with DAC registers
        self.shadowMap = {}
        # "Shadow" flag with
        self.spi4Wire = False
        # General Configuration Registers (PAGE_SET[2:0] = 000)
        self.defaultMap = \
            { \
            "RESET_CONFIG"      : [0x00, 0x58, 0x03, "Chip Reset and Configuration 8.5.1", 0x00, 0x00], \
            # "IO_CONFIG"       : [0x01, 0x18, 0x00, "IO Configuration 8.5.2", 0x00, 0x00], \
            # ***Added 4-Wire SPI bit to default configuration***
            "IO_CONFIG"         : [0x01, 0x18, 0x80, "IO Configuration 8.5.2", 0x00, 0x00], \
            "ALM_SD_MASK"       : [0x02, 0xFF, 0xFF, "Lane Signal Detect Alarm Mask 8.5.3", 0x00, 0x00], \
            "ALM_CLK_MASK"      : [0x03, 0xFF, 0xFF, "Clock Alarms Mask 8.5.4", 0x00, 0x00], \
            "ALM_SD_DET"        : [0x04, 0x00, 0x00, "SERDES Loss of Signal Detection Alarms 8.5.5", 0x00, 0x00], \
            "ALM_SYSREF_DET"    : [0x05, 0x00, 0x00, "SYSREF Alignment Circuit Alarms 8.5.6", 0x00, 0x00], \
            "TEMP_PLLVOLT"      : [0x06, 0x00, 0x00, " Temperature Sensor and PLL Loop Voltage 8.5.7", 0x00, 0x00], \
            "PAGE_SET"          : [0x09, 0x00, 0x00, "Page Set ", 0x00, 0x00], \
            "SYSREF_ALIGN_R"    : [0x78, 0x00, 0x00, "SYSERF Align to r1 and r3 Count 8.5.9", 0x00, 0x00], \
            "SYSREF12_CNT"      : [0x79, 0x00, 0x00, "SYSREF Phase Count 1 and 2 8.5.10", 0x00, 0x00], \
            "SYSREF34_CNT"      : [0x7A, 0x00, 0x00, "SYSREF Phase Count 3 and 4", 0x00, 0x00], \
            "VENDOR_VER"        : [0x7F, 0x00, 0x09, "Vendor ID and Chip Version", 0x00, 0x00], \
            # Multi-DUC Configuration Registers (PAGE_SET[0] = 1 for multi-DUC1, PAGE_SET[1] = 1 for multi-DUC2)
            "MULTIDUC_CFG1"     : [0x0A, 0x02, 0xB0, "Multi-DUC Configuration (PAP, Interpolation) ", 0x01, 0x02], \
            "MULTIDUC_CFG2"     : [0x0C, 0x24, 0x02, "Multi-DUC Configuration (Mixers) 8.5.14", 0x01, 0x02], \
            "JESD_FIFO"         : [0x0D, 0x80, 0x00, "JESD FIFO Control 8.5.15", 0x01, 0x02], \
            "ALM_MASK1"         : [0x0E, 0x00, 0xFF, "Alarm Mask 1 8.5.16", 0x01, 0x02], \
            "ALM_MASK2"         : [0x0F, 0xFF, 0xFF, "Alarm Mask 2 8.5.17", 0x01, 0x02], \
            "ALM_MASK3"         : [0x10, 0xFF, 0xFF, "Alarm Mask 3 8.5.18", 0x01, 0x02], \
            "ALM_MASK4"         : [0x11, 0xFF, 0xFF, "Alarm Mask 4 8.5.19", 0x01, 0x02], \
            "JESD_LN_SKEW"      : [0x12, 0x00, 0x00, "JESD Lane Skew 8.5.20", 0x01, 0x02], \
            "CMIX"              : [0x17, 0x00, 0x00, "CMIX Configuration", 0x01, 0x02], \
            "OUTSUM"            : [0x19, 0x00, 0x00, "Output Summation and Delay", 0x01, 0x02], \
            "PHASE_NCOAB"       : [0x1C, 0x00, 0x00, "Phase offset for AB path NCO 8.5.23", 0x01, 0x02], \
            "PHASE_NCOCD"       : [0x1D, 0x00, 0x00, "Phase offset for CD path NCO 8.5.24", 0x01, 0x02], \
            "FREQ_NCOAB1"       : [0x1E, 0x00, 0x00, "0x1E-0x20 0x0000 FREQ_NCOAB Frequency for AB path NCO 8.5.25", 0x01, 0x02], \
            "FREQ_NCOAB2"       : [0x1F, 0x00, 0x00, "FREQ_NCOAB", 0x01, 0x02], \
            "FREQ_NCOAB3"       : [0x20, 0x00, 0x00, "FREQ_NCOAB", 0x01, 0x02], \
            "FREQ_NCOCD1"       : [0x21, 0x00, 0x00, "0x21-0x23 0x0000 FREQ_NCOCD Frequency for CD path NCO 8.5.26", 0x01, 0x02], \
            "FREQ_NCOCD2"       : [0x22, 0x00, 0x00, "FREQ_NCOCD", 0x01, 0x02], \
            "FREQ_NCOCD3"       : [0x23, 0x00, 0x00, "FREQ_NCOCD", 0x01, 0x02], \
            "SYSREF_CLKDIV"     : [0x24, 0x00, 0x10, "SYSREF Use for Clock Divider 8.5.27", 0x01, 0x02], \
            "SERDES_CLK"        : [0x25, 0x77, 0x00, "Serdes Clock Control 8.5.28", 0x01, 0x02], \
            "SYNCSEL1"          : [0x27, 0x11, 0x44, "Sync Source Selection 8.5.29", 0x01, 0x02], \
            "SYNCSEL2"          : [0x28, 0x00, 0x00, "Sync Source Selection 8.5.30", 0x01, 0x02], \
            "PAP_GAIN_AB"       : [0x29, 0x00, 0x00, "PAP path AB Gain Attenuation Step 8.5.31", 0x01, 0x02], \
            "PAP_WAIT_AB"       : [0x2A, 0x00, 0x00, "PAP path AB Wait Time at Gain = 0 8.5.32", 0x01, 0x02], \
            "PAP_GAIN_CD"       : [0x2B, 0x00, 0x00, "PAP path CD Gain Attenuation Step 8.5.33", 0x01, 0x02], \
            "PAP_WAIT_CD"       : [0x2C, 0x00, 0x00, "PAP path CD Wait Time at Gain = 0 8.5.34", 0x01, 0x02], \
            "PAP_CFG_AB"        : [0x2D, 0x1F, 0xFF, "PAP path AB Configuration 8.5.35", 0x01, 0x02], \
            "PAP_CFG_CD"        : [0x2E, 0x1F, 0xFF, "PAP path CD Configuration 8.5.36", 0x01, 0x02], \
            "SPIDAC_TEST1"      : [0x2F, 0x00, 0x00, "Configuration for DAC SPI Constant 8.5.37", 0x01, 0x02], \
            "SPIDAC_TEST2"      : [0x30, 0x00, 0x00, "DAC SPI Constant 8.5.38", 0x01, 0x02], \
            "GAINAB"            : [0x32, 0x04, 0x00, "Gain for path AB 8.5.39", 0x01, 0x02], \
            "GAINCD"            : [0x33, 0x04, 0x00, "Gain for path CD 8.5.40", 0x01, 0x02], \
            "JESD_ERR_CNT"      : [0x41, 0x00, 0x00, "JESD Error Counter", 0x01, 0x02], \
            "JESD_ID1"          : [0x46, 0x00, 0x44, "JESD ID 1 8.5.42", 0x01, 0x02], \
            "JESD_ID2"          : [0x47, 0x19, 0x0A, "JESD ID 2 8.5.43", 0x01, 0x02], \
            "JESD_ID3"          : [0x48, 0x31, 0xC3, "JESD ID 3 and Subclass 8.5.44", 0x01, 0x02], \
            "JESD_LN_EN"        : [0x4A, 0x00, 0x03, "JESD Lane Enable 8.5.45", 0x01, 0x02], \
            "JESD_RBD_F"        : [0x4B, 0x13, 0x00, "JESD RBD Buffer and Frame Octets 8.5.46", 0x01, 0x02], \
            "JESD_K_L"          : [0x4C, 0x13, 0x03, "JESD K and L Parameters 8.5.47", 0x01, 0x02], \
            "JESD_M_S"          : [0x4D, 0x01, 0x00, "JESD M and S Parameters 8.5.48", 0x01, 0x02], \
            "JESD_N_HD_SCR"     : [0x4E, 0x0F, 0x4F, "JESD N, HD and SCR Parameters 8.5.49", 0x01, 0x02], \
            "JESD_MATCH"        : [0x4F, 0x1C, 0xC1, "JESD Character Match and Other 8.5.50", 0x01, 0x02], \
            "JESD_LINK_CFG"     : [0x50, 0x00, 0x00, "JESD Link Configuration Data 8.5.51", 0x01, 0x02], \
            "JESD_SYNC_REQ"     : [0x51, 0x00, 0xFF, "JESD Sync Request 8.5.52", 0x01, 0x02], \
            "JESD_ERR_OUT"      : [0x52, 0x00, 0xFF, "JESD Error Output 8.5.53", 0x01, 0x02], \
            "JESD_ILA_CFG1"     : [0x53, 0x01, 0x00, "JESD Configuration Value used for ILA", 0x01, 0x02], \
            "JESD_ILA_CFG2"     : [0x54, 0x8E, 0x60, "JESD Configuration Value used for ILA", 0x01, 0x02], \
            "JESD_SYSR_MODE"    : [0x5C, 0x00, 0x01, "JESD SYSREF Mode", 0x01, 0x02], \
            "JESD_CROSSBAR1"    : [0x5F, 0x01, 0x23, "JESD Crossbar Configuration 1 8.5.57", 0x01, 0x02], \
            "JESD_CROSSBAR2"    : [0x60, 0x45, 0x67, "JESD Crossbar Configuration 2 8.5.58", 0x01, 0x02], \
            "JESD_ALM_L0"       : [0x64, 0x00, 0x00, "JESD Alarms for Lane 0 8.5.59", 0x01, 0x02], \
            "JESD_ALM_L1"       : [0x65, 0x00, 0x00, "JESD Alarms for Lane 1 8.5.60", 0x01, 0x02], \
            "JESD_ALM_L2"       : [0x66, 0x00, 0x00, "JESD Alarms for Lane 2 8.5.61", 0x01, 0x02], \
            "JESD_ALM_L7"       : [0x6B, 0x00, 0x00, "JESD Alarms for Lane 7 8.5.66", 0x01, 0x02], \
            "JESD_ALM_L3"       : [0x67, 0x00, 0x00, "JESD Alarms for Lane 3 8.5.62", 0x01, 0x02], \
            "JESD_ALM_L4"       : [0x68, 0x00, 0x00, "JESD Alarms for Lane 4 8.5.63", 0x01, 0x02], \
            "JESD_ALM_L5"       : [0x69, 0x00, 0x00, "JESD Alarms for Lane 5 8.5.64", 0x01, 0x02], \
            "JESD_ALM_L6"       : [0x6A, 0x00, 0x00, "JESD Alarms for Lane 6 8.5.65", 0x01, 0x02], \
            "ALM_SYSREF_PAP"    : [0x6C, 0x00, 0x00, "SYSREF and PAP Alarms 8.5.67", 0x01, 0x02], \
            "ALM_CLKDIV1"       : [0x6D, 0x00, 0x00, "Clock Divider Alarms 1 8.5.68", 0x01, 0x02], \
            # Miscellaneous Configuration Registers (PAGE_SET[1:0] = 00, PAGE_SET[2] = 1)
            "CLK_CONFIG"        : [0x0A, 0xFC, 0x03, "Clock Configuration 8.5.69", 0x04, 0x04], \
            "SLEEP_CONFIG"      : [0x0B, 0x00, 0x22, "Sleep Configuration 8.5.70", 0x04, 0x04], \
            "CLK_OUT"           : [0x0C, 0xA0, 0x02, "Divided Output Clock Configuration 8.5.71", 0x04, 0x04], \
            "DACFS"             : [0x0D, 0xF0, 0x00, "DAC Fullscale Current 8.5.72", 0x04, 0x04], \
            "LCMGEN"            : [0x10, 0x00, 0x00, "Internal sysref generator 8.5.73", 0x04, 0x04], \
            "LCMGEN_DIV"        : [0x11, 0x00, 0x00, "Counter for internal sysref generator 8.5.74", 0x04, 0x04], \
            "LCMGEN_SPISYSREF"  : [0x12, 0x00, 0x00, "SPI SYSREF for internal sysref generator 8.5.75", 0x04, 0x04], \
            "DTEST"             : [0x1B, 0x00, 0x00, "Digital Test Signals", 0x04, 0x04], \
            "SLEEP_CNTL"        : [0x23, 0xFF, 0xFF, "Sleep Pin Control 8.5.77", 0x04, 0x04], \
            "SYSR_CAPTURE"      : [0x24, 0x10, 0x00, "SYSREF Capture Circuit Control 8.5.78", 0x04, 0x04], \
            "CLK_PLL_CFG"       : [0x31, 0x02, 0x00, "Clock Input and PLL Configuration 8.5.79", 0x04, 0x04], \
            "PLL_CONFIG1"       : [0x32, 0x03, 0x08, "PLL Configuration 1 8.5.80", 0x04, 0x04], \
            "PLL_CONFIG2"       : [0x33, 0x40, 0x18, "PLL Configuration 2 8.5.81", 0x04, 0x04], \
            "LVDS_CONFIG"       : [0x34, 0x00, 0x00, "LVDS Output Configuration 8.5.82", 0x04, 0x04], \
            "PLL_FDIV"          : [0x35, 0x00, 0x18, "Fuse farm clock divider 8.5.83", 0x04, 0x04], \
            "SRDS_CLK_CFG"      : [0x3B, 0x18, 0x02, "Serdes Clock Configuration 8.5.84", 0x04, 0x04], \
            "SRDS_PLL_CFG"      : [0x3C, 0x82, 0x28, "Serdes PLL Configuration 8.5.85", 0x04, 0x04], \
            "SRDS_CFG1"         : [0x3D, 0x00, 0x88, "Serdes Configuration 1 8.5.86", 0x04, 0x04], \
            "SRDS_CFG2"         : [0x3E, 0x09, 0x09, "Serdes Configuration 2 8.5.87", 0x04, 0x04], \
            "SRDS_POL"          : [0x3F, 0x00, 0x00, "Serdes Polarity Control 8.5.88", 0x04, 0x04], \
            "SYNCBOUT"          : [0x76, 0x00, 0x00, "JESD204B SYNCB Output", 0x04, 0x04], \
            }
        # read all registers on
        # self.refreshShadow()
    def getDUC(self):
        return self.multiDUC
    def getAddress(self, name):
        if name in self.defaultMap:
            addr = self.defaultMap[name][0]
            self.debugPrint( "getAddress: "+name+", "+hex(addr)+" -> " )
            return addr
    def getDefaultUpper(self, name):
        if name in self.defaultMap:
            return self.defaultMap[name][1]
    def getDefaultLower(self, name):
        if name in self.defaultMap:
            return self.defaultMap[name][2]
    def getInfo(self, name):
        if name in self.defaultMap:
            return self.defaultMap[name][3]
    def getPage(self, name):
        if name in self.defaultMap:
            if self.multiDUC == 1:
                page = self.defaultMap[name][4]
                self.debugPrint( "getPage: "+name+", "+hex(page)+" -> " )
                return page
            if self.multiDUC == 2:
                page = self.defaultMap[name][5]
                self.debugPrint( "getPage: "+name+", "+hex(page)+" -> " )
                return page
    def writeReg(self, name, upper=0x00, lower=0x00):
        self.debugPrint( "writeReg -> " )
        addr = self.getAddress(name)
        self.debugPrint( "writeReg: "+hex(addr)+", "+hex(upper)+", "+hex(lower), end='\n' )
        self.slave.exchange( \
            out = [ \
                addr, \
                upper, \
                lower \
            ], \
            readlen=0, \
            start=True, \
            stop=True, \
            duplex=False, \
            droptail=0 \
        )
    def readReg(self, name):
        self.debugPrint( "readReg -> " )
        addr = self.getAddress(name)
        readMask = 0x80
        data = self.slave.exchange( \
            out=[ (addr | readMask) ], \
            readlen=2, \
            start=True, \
            stop=True, \
            duplex=False, \
            droptail=0 \
        )
        if data:
            self.debugPrint( "readReg: "+hex(addr)+", "+hex(data[0])+", "+hex(data[1]), end='\n' )
            return data
        else:
            self.debugPrint( "readReg: "+hex(addr)+", NO DATA!", end='\n' )
            return [0x00, 0x00]
    def enableReading(self):
        self.debugPrint( "enableReading -> " )
        # set 4-wire SPI mode
        self.writeReg("IO_CONFIG", 0x18, 0x80)
        self.spi4Wire = True
    def setDUC(self, duc):
        self.multiDUC = duc
        self.debugPrint( "setDUC: "+str(self.multiDUC), end='\n' )
    def setPage(self, name):
        self.debugPrint( "setPage -> " )
        page = self.getPage(name)
        self.debugPrint( "setPage -> " )
        self.writeReg("PAGE_SET", 0x00, page)
    def writePageReg(self, name, upper=0x00, lower=0x00):
        self.debugPrint( "writePageReg -> " )
        addr = self.getAddress(name)
        if addr:
            self.setPage(name)
            return self.writeReg(name, upper, lower)
    def readPageReg(self, name):
        self.debugPrint( "readPageReg -> " )
        self.enableReading()
        self.debugPrint( "readPageReg -> " )
        self.setPage(name)
        self.debugPrint( "readPageReg -> " )
        return self.readReg(name)
    def writeReadPageReg(self, name, upper=0x00, lower=0x00):
        self.debugPrint( "writeReadPageReg -> " )
        self.setPage(name)
        self.debugPrint( "writeReadPageReg -> " )
        self.writePageReg(name, upper, lower)
        self.debugPrint( "writeReadPageReg -> " )
        return self.readPageReg(name)
    def bitsOn(self, name, upperBitMask=0x00, lowerBitMask=0x00):
        self.debugPrint( "bitOn -> " )
        currentState = self.readPageReg(name)
        self.debugPrint( "bitOn -> " )
        return self.writeReadPageReg(name, currentState[0] | upperBitMask, currentState[1] | lowerBitMask)
    def bitsOff(self, name, upperBitMask=0x00, lowerBitMask=0x00):
        self.debugPrint( "bitOff -> " )
        currentState = self.readPageReg(name)
        self.debugPrint( "bitOff -> " )
        return self.writeReadPageReg(name, currentState[0] & ~upperBitMask, currentState[1] & ~lowerBitMask)
    def outDefList(self):
        regNames = []
        for name in self.defaultMap.keys():
            regNames.append(name)
        return regNames
    def inNameOutRegData(self, name):
        regData = {}
        if name in self.defaultMap.keys():
            regData['data'] = self.readPageReg(name) # returns list
            regData['addr'] = [ self.getAddress(name) ]
            regData['page'] = [ self.getPage(name) ]
            regData['info'] = self.getInfo(name)
        return regData
    def inNameOutDefData(self, name):
        regData = {}
        if name in self.defaultMap.keys():
            regData['data'] = [ self.defaultMap[name][1], self.defaultMap[name][2] ]
            regData['addr'] = [ self.defaultMap[name][0] ]
            if self.multiDUC == 1:
                regData['page'] = [ self.defaultMap[name][4] ]
            else:
                regData['page'] = [ self.defaultMap[name][5] ]
            regData['info'] = self.defaultMap[name][3]
        return regData
    def inListOutFuncData(self, regList, func):
        regData = {}
        for name in regList:
            if name in self.defaultMap.keys():
                regData[name] = func(name)
        return regData
    def outRegData(self):
        return self.inListOutFuncData(self.outDefList(), self.inNameOutRegData)
    def outDefData(self):
        return self.inListOutFuncData(self.outDefList(), self.inNameOutDefData)
    def inRangeOutFuncData(self, start, stop, func):
        subList = []
        isPartOfList = False
        for reg in self.outDefList():
            if reg == start:
                isPartOfList = True
            if reg == stop:
                isPartOfList = False
            if isPartOfList:
                subList.append(reg)
        return self.inListOutFuncData(subList, func)
    def inRangeOutRegData(self, start, stop):
        return self.inRangeOutFuncData(start, stop, self.inNameOutRegData)
    def debugPrint(self, debugNote, end=''):
        if self.debugFlag:
            print(debugNote, end=end)
    def inDataOutRegData(self, inputData):
        outputData = {}
        for reg in inputData:
            outputData[reg] = self.inNameOutRegData(reg)
            if 'data' in inputData[reg]: # data exists to write
                if 'mask' in inputData[reg]:
                    self.writePageReg(reg, \
                        (outputData[reg]['data'][0] & ~inputData[reg]['mask'][0]) | inputData[reg]['data'][0], \
                        (outputData[reg]['data'][1] & ~inputData[reg]['mask'][1]) | inputData[reg]['data'][1] \
                    )
                else:
                    self.writePageReg(reg, inputData[reg]['data'][0], inputData[reg]['data'][1])
                outputData[reg]['new_data'] = self.readPageReg(reg)
        return outputData
