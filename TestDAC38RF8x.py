import DAC38RF8x
from regdisplay import *
import JSONFile

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

jfile = JSONFile.new("DAC38RF8x.json")
jfile.write(dacSpi.outDefData())

print( "-----------------------------------\nDisplay all registers:" )
printData( dacSpi.outRegData())

print( "-----------------------------------\nLoad defaults:" )
printData( dacSpi.inDataOutRegData(dacSpi.outDefData()) )


# sequence data
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

print( "-----------------------------------\nLoad sequence:" )
printData( dacSpi.inDataOutRegData(newSeq) )


print( "-----------------------------------\nDisplay all registers:" )
printData( dacSpi.outRegData())



# print( "-----------------------------------\nDUC 1:" )
# regData = dacSpi.outRegData()
# printData(regData)


# dacSpi.setDUC(2)
#
# print( "-----------------------------------\nDUC 2:" )
# regData = dacSpi.readDataAll()
# printRegData(regData)
