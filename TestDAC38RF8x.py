import DAC38RF8x
from regdisplay import *

##########################################
# Test DAC38RF8x module
##########################################



# dacSpi = DAC38RF8x.SpiConfig(debugFlag=True)
# dacSpi.setDUC(1)
# dacSpi.readPageReg("PAGE_SET")
# dacSpi.setDUC(2)
# dacSpi.readPageReg("PAGE_SET")
#
# dacSpi.setDUC(2)
# dacSpi.bitsOff("ALM_MASK1", 0x00, 0x0F)
# dacSpi.setDUC(1)
# dacSpi.bitsOn("ALM_MASK1", 0x00, 0x0F)



dacSpi = DAC38RF8x.SpiConfig()

newSeq = {                          \
    'ALM_MASK1' : {                 \
        'mask' : [ 0x00, 0xFF ],    \
        'data' : [ 0x00, 0x01 ],    \
    },                              \
    'ALM_MASK2' : {                 \
        'mask' : [ 0x00, 0xFF ],    \
        'data' : [ 0x00, 0x0F ],    \
    },                              \
    'JESD_FIFO' : {},               \
    'VENDOR_VER' : {}               \
}


newData = dacSpi.action(newSeq)
printData(newData)




print( "-----------------------------------\nDUC 1:" )
regData = dacSpi.readDataAll()
printData(regData)


# dacSpi.setDUC(2)
#
# print( "-----------------------------------\nDUC 2:" )
# regData = dacSpi.readDataAll()
# printRegData(regData)
