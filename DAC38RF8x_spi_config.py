from pyftdi.spi import SpiController
import time
import sys


##########################################
# Basic R/W
##########################################








class DACConfig:
    def __init__(self, ftdiDevice='ftdi:///2', multiDUCMask=0x01):
        self.ftdiDevice = ftdiDevice
        self.multiDUCMask = multiDUCMask
        # Instantiate a SPI controller
        self.spi = SpiController()
        # Configure the first interface (IF/1) of the FTDI device as a SPI master
        self.spi.configure(self.ftdiDevice)
        # Get a port to a SPI slave w/ /CS on A*BUS3 and SPI mode 0 @ 12MHz
        self.slave = spi.get_port(cs=0, freq=1E6, mode=0)
        # "Shadow" register map -- tries to stay in sync with DAC registers
        self.shadowMap = {}
        # General Configuration Registers (PAGE_SET[2:0] = 000)
        self.defaultMap = [ \
            { \
            "RESET_CONFIG"      : [0x00, 0x58, 0x03, "Chip Reset and Configuration 8.5.1", 0x00], \
            # "IO_CONFIG"       : [0x01, 0x18, 0x00, "IO Configuration 8.5.2", 0x00], \
            # ***Added 4-Wire SPI bit to default configuration***
            "IO_CONFIG"         : [0x01, 0x18, 0x80, "IO Configuration 8.5.2", 0x00], \
            "ALM_SD_MASK"       : [0x02, 0xFF, 0xFF, "Lane Signal Detect Alarm Mask 8.5.3", 0x00], \
            "ALM_CLK_MASK"      : [0x03, 0xFF, 0xFF, "Clock Alarms Mask 8.5.4", 0x00], \
            "ALM_SD_DET"        : [0x04, 0x00, 0x00, "SERDES Loss of Signal Detection Alarms 8.5.5", 0x00], \
            "ALM_SYSREF_DET"    : [0x05, 0x00, 0x00, "SYSREF Alignment Circuit Alarms 8.5.6", 0x00], \
            "TEMP_PLLVOLT"      : [0x06, 0x00, 0x00, " Temperature Sensor and PLL Loop Voltage 8.5.7", 0x00], \
            "PAGE_SET"          : [0x09, 0x00, 0x00, "Page Set ", 0x00], \
            "SYSREF_ALIGN_R"    : [0x78, 0x00, 0x00, "SYSERF Align to r1 and r3 Count 8.5.9", 0x00], \
            "SYSREF12_CNT"      : [0x79, 0x00, 0x00, "SYSREF Phase Count 1 and 2 8.5.10", 0x00], \
            "SYSREF34_CNT"      : [0x7A, 0x00, 0x00, "SYSREF Phase Count 3 and 4", 0x00], \
            "VENDOR_VER"        : [0x7F, 0x00, 0x09, "Vendor ID and Chip Version", 0x00], \
            # Multi-DUC Configuration Registers (PAGE_SET[0] = 1 for multi-DUC1, PAGE_SET[1] = 1 for multi-DUC2)
            "MULTIDUC_CFG1"     : [0x0A, 0x02, 0xB0, "Multi-DUC Configuration (PAP, Interpolation) ", self.multiDUCMask], \
            "MULTIDUC_CFG2"     : [0x0C, 0x24, 0x02, "Multi-DUC Configuration (Mixers) 8.5.14", self.multiDUCMask], \
            "JESD_FIFO"         : [0x0D, 0x80, 0x00, "JESD FIFO Control 8.5.15", self.multiDUCMask], \
            "ALM_MASK1"         : [0x0E, 0x00, 0xFF, "Alarm Mask 1 8.5.16", self.multiDUCMask], \
            "ALM_MASK2"         : [0x0F, 0xFF, 0xFF, "Alarm Mask 2 8.5.17", self.multiDUCMask], \
            "ALM_MASK3"         : [0x10, 0xFF, 0xFF, "Alarm Mask 3 8.5.18", self.multiDUCMask], \
            "ALM_MASK4"         : [0x11, 0xFF, 0xFF, "Alarm Mask 4 8.5.19", self.multiDUCMask], \
            "JESD_LN_SKEW"      : [0x12, 0x00, 0x00, "JESD Lane Skew 8.5.20", self.multiDUCMask], \
            "CMIX"              : [0x17, 0x00, 0x00, "CMIX Configuration", self.multiDUCMask], \
            "OUTSUM"            : [0x19, 0x00, 0x00, "Output Summation and Delay", self.multiDUCMask], \
            "PHASE_NCOAB"       : [0x1C, 0x00, 0x00, "Phase offset for AB path NCO 8.5.23", self.multiDUCMask], \
            "PHASE_NCOCD"       : [0x1D, 0x00, 0x00, "Phase offset for CD path NCO 8.5.24", self.multiDUCMask], \
            "FREQ_NCOAB1"       : [0x1E, 0x00, 0x00, "0x1E-0x20 0x0000 FREQ_NCOAB Frequency for AB path NCO 8.5.25", self.multiDUCMask], \
            "FREQ_NCOAB2"       : [0x1F, 0x00, 0x00, "FREQ_NCOAB", self.multiDUCMask], \
            "FREQ_NCOAB3"       : [0x20, 0x00, 0x00, "FREQ_NCOAB", self.multiDUCMask], \
            "FREQ_NCOCD1"       : [0x21, 0x00, 0x00, "0x21-0x23 0x0000 FREQ_NCOCD Frequency for CD path NCO 8.5.26", self.multiDUCMask], \
            "FREQ_NCOCD2"       : [0x22, 0x00, 0x00, "FREQ_NCOCD", self.multiDUCMask], \
            "FREQ_NCOCD3"       : [0x23, 0x00, 0x00, "FREQ_NCOCD", self.multiDUCMask], \
            "SYSREF_CLKDIV"     : [0x24, 0x00, 0x10, "SYSREF Use for Clock Divider 8.5.27", self.multiDUCMask], \
            "SERDES_CLK"        : [0x25, 0x77, 0x00, "Serdes Clock Control 8.5.28", self.multiDUCMask], \
            "SYNCSEL1"          : [0x27, 0x11, 0x44, "Sync Source Selection 8.5.29", self.multiDUCMask], \
            "SYNCSEL2"          : [0x28, 0x00, 0x00, "Sync Source Selection 8.5.30", self.multiDUCMask], \
            "PAP_GAIN_AB"       : [0x29, 0x00, 0x00, "PAP path AB Gain Attenuation Step 8.5.31", self.multiDUCMask], \
            "PAP_WAIT_AB"       : [0x2A, 0x00, 0x00, "PAP path AB Wait Time at Gain = 0 8.5.32", self.multiDUCMask], \
            "PAP_GAIN_CD"       : [0x2B, 0x00, 0x00, "PAP path CD Gain Attenuation Step 8.5.33", self.multiDUCMask], \
            "PAP_WAIT_CD"       : [0x2C, 0x00, 0x00, "PAP path CD Wait Time at Gain = 0 8.5.34", self.multiDUCMask], \
            "PAP_CFG_AB"        : [0x2D, 0x1F, 0xFF, "PAP path AB Configuration 8.5.35", self.multiDUCMask], \
            "PAP_CFG_CD"        : [0x2E, 0x1F, 0xFF, "PAP path CD Configuration 8.5.36", self.multiDUCMask], \
            "SPIDAC_TEST1"      : [0x2F, 0x00, 0x00, "Configuration for DAC SPI Constant 8.5.37", self.multiDUCMask], \
            "SPIDAC_TEST2"      : [0x30, 0x00, 0x00, "DAC SPI Constant 8.5.38", self.multiDUCMask], \
            "GAINAB"            : [0x32, 0x04, 0x00, "Gain for path AB 8.5.39", self.multiDUCMask], \
            "GAINCD"            : [0x33, 0x04, 0x00, "Gain for path CD 8.5.40", self.multiDUCMask], \
            "JESD_ERR_CNT"      : [0x41, 0x00, 0x00, "JESD Error Counter", self.multiDUCMask], \
            "JESD_ID1"          : [0x46, 0x00, 0x44, "JESD ID 1 8.5.42", self.multiDUCMask], \
            "JESD_ID2"          : [0x47, 0x19, 0x0A, "JESD ID 2 8.5.43", self.multiDUCMask], \
            "JESD_ID3"          : [0x48, 0x31, 0xC3, "JESD ID 3 and Subclass 8.5.44", self.multiDUCMask], \
            "JESD_LN_EN"        : [0x4A, 0x00, 0x03, "JESD Lane Enable 8.5.45", self.multiDUCMask], \
            "JESD_RBD_F"        : [0x4B, 0x13, 0x00, "JESD RBD Buffer and Frame Octets 8.5.46", self.multiDUCMask], \
            "JESD_K_L"          : [0x4C, 0x13, 0x03, "JESD K and L Parameters 8.5.47", self.multiDUCMask], \
            "JESD_M_S"          : [0x4D, 0x01, 0x00, "JESD M and S Parameters 8.5.48", self.multiDUCMask], \
            "JESD_N_HD_SCR"     : [0x4E, 0x0F, 0x4F, "JESD N, HD and SCR Parameters 8.5.49", self.multiDUCMask], \
            "JESD_MATCH"        : [0x4F, 0x1C, 0xC1, "JESD Character Match and Other 8.5.50", self.multiDUCMask], \
            "JESD_LINK_CFG"     : [0x50, 0x00, 0x00, "JESD Link Configuration Data 8.5.51", self.multiDUCMask], \
            "JESD_SYNC_REQ"     : [0x51, 0x00, 0xFF, "JESD Sync Request 8.5.52", self.multiDUCMask], \
            "JESD_ERR_OUT"      : [0x52, 0x00, 0xFF, "JESD Error Output 8.5.53", self.multiDUCMask], \
            "JESD_ILA_CFG1"     : [0x53, 0x01, 0x00, "JESD Configuration Value used for ILA", self.multiDUCMask], \
            "JESD_ILA_CFG2"     : [0x54, 0x8E, 0x60, "JESD Configuration Value used for ILA", self.multiDUCMask], \
            "JESD_SYSR_MODE"    : [0x5C, 0x00, 0x01, "JESD SYSREF Mode", self.multiDUCMask], \
            "JESD_CROSSBAR1"    : [0x5F, 0x01, 0x23, "JESD Crossbar Configuration 1 8.5.57", self.multiDUCMask], \
            "JESD_CROSSBAR2"    : [0x60, 0x45, 0x67, "JESD Crossbar Configuration 2 8.5.58", self.multiDUCMask], \
            "JESD_ALM_L0"       : [0x64, 0x00, 0x00, "JESD Alarms for Lane 0 8.5.59", self.multiDUCMask], \
            "JESD_ALM_L1"       : [0x65, 0x00, 0x00, "JESD Alarms for Lane 1 8.5.60", self.multiDUCMask], \
            "JESD_ALM_L2"       : [0x66, 0x00, 0x00, "JESD Alarms for Lane 2 8.5.61", self.multiDUCMask], \
            "JESD_ALM_L7"       : [0x6B, 0x00, 0x00, "JESD Alarms for Lane 7 8.5.66", self.multiDUCMask], \
            "JESD_ALM_L3"       : [0x67, 0x00, 0x00, "JESD Alarms for Lane 3 8.5.62", self.multiDUCMask], \
            "JESD_ALM_L4"       : [0x68, 0x00, 0x00, "JESD Alarms for Lane 4 8.5.63", self.multiDUCMask], \
            "JESD_ALM_L5"       : [0x69, 0x00, 0x00, "JESD Alarms for Lane 5 8.5.64", self.multiDUCMask], \
            "JESD_ALM_L6"       : [0x6A, 0x00, 0x00, "JESD Alarms for Lane 6 8.5.65", self.multiDUCMask], \
            "ALM_SYSREF_PAP"    : [0x6C, 0x00, 0x00, "SYSREF and PAP Alarms 8.5.67", self.multiDUCMask], \
            "ALM_CLKDIV1"       : [0x6D, 0x00, 0x00, "Clock Divider Alarms 1 8.5.68", self.multiDUCMask], \
            # Miscellaneous Configuration Registers (PAGE_SET[1:0] = 00, PAGE_SET[2] = 1)
            "CLK_CONFIG"        : [0x0A, 0xFC, 0x03, "Clock Configuration 8.5.69", 0x04], \
            "SLEEP_CONFIG"      : [0x0B, 0x00, 0x22, "Sleep Configuration 8.5.70", 0x04], \
            "CLK_OUT"           : [0x0C, 0xA0, 0x02, "Divided Output Clock Configuration 8.5.71", 0x04], \
            "DACFS"             : [0x0D, 0xF0, 0x00, "DAC Fullscale Current 8.5.72", 0x04], \
            "LCMGEN"            : [0x10, 0x00, 0x00, "Internal sysref generator 8.5.73", 0x04], \
            "LCMGEN_DIV"        : [0x11, 0x00, 0x00, "Counter for internal sysref generator 8.5.74", 0x04], \
            "LCMGEN_SPISYSREF"  : [0x12, 0x00, 0x00, "SPI SYSREF for internal sysref generator 8.5.75", 0x04], \
            "DTEST"             : [0x1B, 0x00, 0x00, "Digital Test Signals", 0x04], \
            "SLEEP_CNTL"        : [0x23, 0xFF, 0xFF, "Sleep Pin Control 8.5.77", 0x04], \
            "SYSR_CAPTURE"      : [0x24, 0x10, 0x00, "SYSREF Capture Circuit Control 8.5.78", 0x04], \
            "CLK_PLL_CFG"       : [0x31, 0x02, 0x00, "Clock Input and PLL Configuration 8.5.79", 0x04], \
            "PLL_CONFIG1"       : [0x32, 0x03, 0x08, "PLL Configuration 1 8.5.80", 0x04], \
            "PLL_CONFIG2"       : [0x33, 0x40, 0x18, "PLL Configuration 2 8.5.81", 0x04], \
            "LVDS_CONFIG"       : [0x34, 0x00, 0x00, "LVDS Output Configuration 8.5.82", 0x04], \
            "PLL_FDIV"          : [0x35, 0x00, 0x18, "Fuse farm clock divider 8.5.83", 0x04], \
            "SRDS_CLK_CFG"      : [0x3B, 0x18, 0x02, "Serdes Clock Configuration 8.5.84", 0x04], \
            "SRDS_PLL_CFG"      : [0x3C, 0x82, 0x28, "Serdes PLL Configuration 8.5.85", 0x04], \
            "SRDS_CFG1"         : [0x3D, 0x00, 0x88, "Serdes Configuration 1 8.5.86", 0x04], \
            "SRDS_CFG2"         : [0x3E, 0x09, 0x09, "Serdes Configuration 2 8.5.87", 0x04], \
            "SRDS_POL"          : [0x3F, 0x00, 0x00, "Serdes Polarity Control 8.5.88", 0x04], \
            "SYNCBOUT"          : [0x76, 0x00, 0x00, "JESD204B SYNCB Output", 0x04], \
            }, \
        ]
    def writeReg(name, upper=0x00, lower=0x00, cs_start=True, cs_stop=True):
        if name in self.defaultMap:
            self.slave.exchange( \
                out = [ \
                    self.defaultMap[name][0], \
                    upper, \
                    lower \
                , 0x00], \ ###################### why is this here????
                readlen=0, \
                start=cs_start, \
                stop=cs_stop, \
                duplex=False, \
                droptail=0 \
            )
    def readReg(name, cs_start=True, cs_stop=True):
        if name in self.defaultMap:
            return self.slave.exchange( \
                out=[ (reg | 0x80) , 0x00], \  #################### why is the 0x00 here?????
                readlen=2, \
                start=cs_start, \
                stop=cs_stop, \
                duplex=False, \
                droptail=0 \
            )
    def writeReadReg(name, upper=0x00, lower=0x00):
        self.writeReg(name, upper, lower)
        return self.readReg(name)
    def bitOn(name, upperBitMask, lowerBitMask):
        currentState = self.readReg(name)
        self.writeReg(name, currentState[0] | upperBitMask, currentState[1] | lowerBitMask)
        return self.readReg(name)
    def bitOff(name, upperBitMask, lowerBitMask):
        currentState = name.readReg(reg)
        self.writeReg(name, currentState[0] & ~upperBitMask, currentState[1] & ~lowerBitMask)
        return self.readReg(reg)


##########################################
# Formatted printing
##########################################

def printByte(aByte):
    for aBit in range(8):
        if ((aByte >> (7-aBit)) & 0x01):
            print("1 ", end='')
        else:
            print("_ ", end='')

def printHex(aByteArray):
    for aByte in aByteArray:
        print(hex(aByte))

def printReg(addrName, addrByte, twoByteArray, note=""):
    print( addrName+(" "*(18-len(addrName))), end=' ')
    print("0x{:02x}".format(addrByte), end=': ')
    print("0x{:02x}".format(twoByteArray[0]), end=' ')
    print("0x{:02x}".format(twoByteArray[1]), end=' ')
    # print(": ", end='')
    printByte(twoByteArray[0])
    print("  ", end='')
    printByte(twoByteArray[1])
    print(" "+note)


##########################################
# Settings that don't require a read
##########################################

# Enables the 4-wire SPI read mode
def enable4Wire():
    writeReg( 0x01, 0x10, 0x80 )

# Enabled register "pages" for reading/writing
def enablePage(page):
    writeReg( 0x09, 0x00, page )

# Reset all register values
def spiReset():
    writeReg( 0x00, 0x80, 0x00 )

##########################################
# Class to tune VCO
##########################################

def VCO_OK(Tj, LFVOLT):
    if (Tj >= 108 and (LFVOLT == 5 or LFVOLT == 6)):
        return True
    elif (Tj >= 92 and (LFVOLT == 4 or LFVOLT == 5)):
        return True
    elif (Tj >= 26 and (LFVOLT == 3 or LFVOLT == 4)):
        return True
    elif (LFVOLT == 2 or LFVOLT == 3):
        return True
    else:
        return False

class VCOTuner:
    def __init__(self,VCOLow, VCOHigh, VCOInc):
        self.VCOLow = VCOLow
        self.VCOHigh = VCOHigh
        self.VCOInc = VCOInc
        self.VCOFreq = VCOLow
    def value(self):
        return self.VCOFreq
    def tune(self):
        while(1):
            PLL_CONFIG = printRead(0x06)
            writeReg(0x33, self.VCOFreq, PLL_CONFIG[1])
            TEMP_PLLVOLT = readReg(0x06)
            TEMPDATA = TEMP_PLLVOLT[0]
            PLL_LFVOLT = (TEMP_PLLVOLT[1] >> 5)
            # print( ("\b"*100)+"Freq: "+str(self.VCOFreq)+", TEMPTDATA: "+str(TEMPDATA)+", PLL_LFVOLT: "+str(PLL_LFVOLT), end='' )
            print( "Freq: "+str(self.VCOFreq)+", TEMPTDATA: "+str(TEMPDATA)+", PLL_LFVOLT: "+str(PLL_LFVOLT) )
            self.VCOFreq += self.VCOInc
            if (VCO_OK(TEMPDATA, PLL_LFVOLT) or self.VCOFreq >= self.VCOHigh):
                break
        print()


##########################################
# Higher level R/W (takes into account the page)
##########################################

# Print a memory page
def printPage(pageMap, page):
    enablePage(page)
    for key in pageMap.keys():
        printReg( key, pageMap[key][0], readReg( pageMap[key][0] ), note=pageMap[key][3] )

# Print all memory pages
def printAll():
    printPage(pageMap0, 0x00)
    printPage(pageMap1, 0x01)
    if (multiDUC):
        printPage(pageMap1, 0x02)
    printPage(pageMap1, 0x04)


# Print individual register


def printAction(func, reg, page, upper, lower):
    enable4Wire()
    readData = func(reg, upper, lower)
    printReg( reg, readData )
    return readData

def printRead(reg):
    enable4Wire()
    readData = readReg(reg )
    printReg( reg, readData )
    return readData

def rangeAction(func, start, end, upper, lower):
    for aReg in defaultMap:
        if (aReg[0] >= start and aReg[0] <= end):
            printReg( aReg[0], func( aReg[0], upper, lower ), note=aReg[3] )

def rangeRead(start, end):
    for aReg in defaultMap:
        if (aReg[0] >= start and aReg[0] <= end):
            printReg( aReg[0], readReg( aReg[0] ), note=aReg[3] )



def startupSequence():
    enableAll()
    print ("SPI_TXENABLE set to 0 (OR'd with TXENABLE pin)")
    printAction( bitOn, 0x0D, 0x00, 0x01)
    while(1):
        if input("Depress RESETB push-button (press <ENTER>)\n> ") == "cancel":
            return
        reg7F = printRead(0x7F)
        if (reg7F[0] & 0xFC == 0x80): # 0b100000XX
            break
    pllMode = input("Tune PLL? [y/N]\n> ")
    if (pllMode.lower() == "y"):
        t = VCOTuner(0x10, 0x40, 0x01)
        t.tune()
    if input("Start SYSREF generation... (press <ENTER>)\n> ") == "cancel":
        return
    print( "Encoder block in reset...")
    printAction( bitOff, 0x24, 0x00, 0x70)
    printAction( bitOff, 0x5C, 0x00, 0x07)
    printAction( bitOn, 0x0A, 0x80, 0x00)
    if input("Ensure 2 SYSREF edges... (press <ENTER>)\n> ") == "cancel":
        return
    printAction( bitOff, 0x0A, 0x80, 0x00)
    print( "JESD core in reset...")
    printAction( bitOn, 0x00, 0x00, 0x03)
    print( "Synchronizing CDRV and JESD204B blocks...")
    SYSREF_CLKDIV = readReg(0x24)
    printAction( writeReadReg, 0x24, SYSREF_CLKDIV[0], (SYSREF_CLKDIV[1] & ~0x70) | 0x20 ) # X010XXXX
    if input("Ensure 2 SYSREF edges... (press <ENTER>)\n> ") == "cancel":
        return
    printAction( writeReadReg, 0x5C, SYSREF_CLKDIV[0], (SYSREF_CLKDIV[1] & ~0x07) | 0x03 ) # XXXXX011
    if input("Ensure 2 SYSREF edges... (press <ENTER>)\n> ") == "cancel":
        return
    print( "Taking JESD204B core out of reset...")
    printAction( bitOff, 0x00, 0x00, 0x03 )
    if input("Ensure 2 SYSREF edges... (press <ENTER>)\n> ") == "cancel":
        return
    print( "Clearing all DAC alarms...")
    rangeAction( writeReadReg, 0x04, 0x05, 0x00, 0x00)
    rangeAction( writeReadReg, 0x64, 0x6D, 0x00, 0x00)
    if input("Stop SYSREF generation (optional)... (press <ENTER>)\n> ") == "cancel":
        return
    print( "SPI_TXENABLE set to 1 (OR'd with TXENABLE pin)...")
    printAction( bitOn, 0x0D, 0x00, 0x01)
    print( "Done." )


enable4Wire()
enableAll()
# readAll()


print("**** DAC38RF8x SPI Register Config ****")
print()
print("Command set:")
print("write <ADDR> <upperByte> <lowerByte>     | Write register")
print("enable4Wire                              | Enables 4-wire mode (called when program starts)")
print("read <ADDR>                              | Read register (4-wire mode only)")
print("on <ADDR> <upperMask> <lowerMask>        | Set bit to 1 (4-wire mode only)")
print("off <ADDR> <upperMask> <lowerMask>       | Set bit to 0 (4-wire mode only)")
print("readAll                                  | Read all registers")
print("enableAll                                | Enable all register pages")
print("save <fileName>                          | Save registers to a file (4-wire mode only)")
print("load <fileName>                          | Load and write registers from a file")
print("loadDefault                              | Load datasheet default configuration")
print("spiReset                                 | Write 0x80 0x00 to address 0x00")
print("exit                                     | Exit the program")
print()
print()

ui = [""]
while (ui[0] != "exit"):
    print("\n> ", end='')
    ui = sys.stdin.readline().rstrip().split(' ')
    uiVal = [0,0,0]
    for i in range(1, len(ui)):
        uiVal[i-1] = int(ui[i],16)

    if (ui[0] == "read"):
        if uiVal[1] > uiVal[0]:
            rangeRead( uiVal[0], uiVal[1] )
        else:
            printRead( uiVal[0] )
    if (ui[0] == "write"):
        printAction( writeReg, uiVal[0], uiVal[1], uiVal[2] )
    if (ui[0] == "on"):
        printAction( bitOn, uiVal[0], uiVal[1], uiVal[2] )
    if (ui[0] == "off"):
        printAction( bitOff, uiVal[0], uiVal[1], uiVal[2] )
    if (ui[0] == "readAll"):
        readAll()
    if (ui[0] == "save"):
        enableAll()
        outputFile = open(ui[1], "w")
        for aReg in defaultMap:
            regData = readReg( aReg[0] )
            outputFile.write(hex(aReg[0])+","+hex(regData[0])+","+hex(regData[1])+"\n")
        outputFile.close()
    if (ui[0] == "load"):
        enableAll()
        inputFile = open(ui[1], "r")
        inputRegMap = inputFile.readlines()
        for regData in inputRegMap:
            reg = regData.rstrip().split(',')
            writeReg(int(reg[0],16), int(reg[1],16), int(reg[2],16))
        inputFile.close()
        readAll()
    if (ui[0] == "loadDefault"):
        for aReg in defaultMap:
            writeReg(aReg[0], aReg[1], aReg[2])
        enableAll()
        readAll()
    if (ui[0] == "enableAll"):
        enableAll()
        readAll()
    if (ui[0] == "spiReset"):
        spiReset()
    if (ui[0] == "enable4Wire"):
        enable4Wire()
    if (ui[0] == "zeroRange"):
        rangeWrite(writeReadReg, uiVal[0], uiVal[1], 0x00, 0x00)
    if (ui[0] == "startup"):
        startupSequence()
