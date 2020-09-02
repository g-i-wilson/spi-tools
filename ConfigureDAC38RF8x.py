import time
import sys
import DAC38RF8x
from regdisplay import *
import JSONFile

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


def printStep(data):
    printData(dacSpi.inDataOutRegData(data))

def bitMaskToBytes(bitStr):
    bit = 0x80
    bitMask = 0x00
    bitData = 0x00
    for char in bitStr:
        if char == 'X':
            bitMask += bit
        if char == '1':
            bitData += bit
        bit /= 2
    return {'data':bitData, 'mask':bitMask}

def bitData(name, upper, lower):
    upperByte = bitMaskToBytes(upper)
    lowerByte = bitMaskToBytes(lower)
    return { \
        name : { \
            'data': [ upperByte['data'], lowerByte['data'] ], \
            'mask': [ lowerByte['mask'], lowerByte['mask'] ]  \
        } \
    }


def startupSequence():
    ###############################
    print (     "SPI_TXENABLE set to 0 (OR'd with TXENABLE pin)")
    printStep({ \
                'JESD_FIFO'     :{ 'data':[0x00,0x01] }  \
    })
    ###############################
    while(1):
        input(  "Depress RESETB push-button (press <ENTER>)")
        VENDOR_VER = printRead(dacSpi.readPageReg, 'VENDOR_VER')
        if (VENDOR_VER[0] & 0xFC == 0x80): # 0b100000XX
            break
    pllMode = input("Tune PLL? [y/N]\n> ")
    if (pllMode.lower() == "y"):
        t = VCOTuner(0x10, 0x40, 0x01)
        t.tune()
    ###############################
    input(      "Start SYSREF generation... (press <ENTER>)")
    ###############################
    print(      "Encoder block in reset...")
    printStep({ \
        bitData('SYSREF_CLKDIV', 'XXXXXXXX', 'X000XXXX'), \
        bitData('JESD_SYSR_MODE', 'XXXXXXXX', 'XXXXX000'), \
        bitData('MULTIDUC_CFG1', '1XXXXXXX', 'XXXXXXXX') \
    })
    input(      "Ensure 2 SYSREF edges... (press <ENTER>)")
    printStep({ \
                'CLK_CONFIG'    :{ 'data':[0x00,0x00], 'mask':[0x80,0x00] } # 1XXXXXXX XXXXXXXX \
    })
    ###############################
    print(      "JESD core in reset...")
    printStep({
                'RESET_CONFIG'  :{ 'data':[0x00,0x03], 'mask':[0x00,0x03] } # XXXXXXXX XXXXX111 \
    })
    ###############################
    print(      "Synchronizing CDRV and JESD204B blocks...")
    printStep({ \
                'SYSREF_CLKDIV'    :{ 'data':[0x00,0x20], 'mask':[0x80,0x70] } # XXXXXXXX X010XXXX \
    })
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





def ui_hex(str):
    return int(str,16)

dacJSON = None

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

    if (ui[0] == "duc"):
        dacSpi.setDUC(int(ui[1],16))
    if (ui[0] == "read"):
        printRead( dacSpi.readPageReg, ui[1] )
    if (ui[0] == "write"):
        writeData = { ui[1] : { 'data':[ int(ui[2],16), int(ui[3],16) ] } }
        printData( dacSpi.inDataOutRegData(writeData) )
        # printAction( dacSpi.writeReadPageReg, ui[1], int(ui[2],16), int(ui[3],16) )
    if (ui[0] == "writeBits"):
        writeData = { ui[1] : { 'data':[ int(ui[2],16), int(ui[3],16) ], 'mask':[ int(ui[4],16), int(ui[5],16) ] } }
        printData( dacSpi.inDataOutRegData(writeData) )
        # printAction( dacSpi.writeReadPageReg, ui[1], int(ui[2],16), int(ui[3],16) )
    if (ui[0] == "on"):
        printAction( dacSpi.bitsOn, ui[1], int(ui[2],16), int(ui[3],16) )
    if (ui[0] == "off"):
        printAction( dacSpi.bitsOff, ui[1], int(ui[2],16), int(ui[3],16) )
    if (ui[0] == "readAll"):
        printData( dacSpi.outRegData() )
    if (ui[0] == "save"):
        if dacJSON is None:
            if len(ui) > 1:
                dacJSON = JSONFile.new(ui[1])
            else:
                dacJSON = JSONFile.new(input("\nSave as: "))
        dacData = dacSpi.outRegData()
        dacJSON.write( dacData )
        printData( dacSpi.outRegData() )
    if (ui[0] == "load"):
        if dacJSON is None:
            dacJSON = JSONFile.load(ui[1])
        dacSpi.inDataOutRegData(dacJSON.read())
        printData( dacSpi.outRegData() )
    if (ui[0] == "loadDefault"):
        dacSpi.inDataOutRegData(dacSpi.outDefData())
        printData( dacSpi.outRegData() )
    # if (ui[0] == "spiReset"):
        # spiReset()
    # if (ui[0] == "zeroRange"):
    #     # rangeWrite(writeReadReg, uiVal[0], uiVal[1], 0x00, 0x00)
    if (ui[0] == "startup"):
        startupSequence()
