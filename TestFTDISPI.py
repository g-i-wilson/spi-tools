import FTDISPI



dac = FTDISPI.Device(defaultMap="DAC38RF8x.json")


struct = {                          \
    'ALM_MASK1' : {                 \
        'mask' : [ 0x00, 0xFF ],    \
        'data' : [ 0x00, 0x02 ],    \
    },                              \
    'ALM_MASK2' : {                 \
        'mask' : [ 0x00, 0xFF ],    \
        'data' : [ 0x00, 0x04 ],    \
    },                              \
    'JESD_FIFO' : {},               \
    'VENDOR_VER' : {}               \
}


# dac.readStruct(struct)
#
# dac.writeStruct(struct)
#
#
# FTDISPI.printStruct(struct)

dac.writeBits('ALM_MASK1', ['0101XX1X', '1XX11000'])


dac.writeBitsList([
    ['ALM_MASK1', ['XXXX0100', 'XXXXXXXX']],
    ['ALM_MASK2', ['XXXXX010', 'XXXXXXXX']],
    ['ALM_MASK3', ['XXXXXX01', 'XXXXXXXX']],
])


FTDISPI.printStruct(dac.currentState())
