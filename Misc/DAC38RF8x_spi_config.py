import time
import sys
import DAC38RF8x
import printreg

##########################################
# SPI configuration class
##########################################

dacSpi = DAC38RF8x.SpiConfig()


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
