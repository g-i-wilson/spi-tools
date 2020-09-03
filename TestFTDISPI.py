import FTDISPI



dac = FTDISPI.Device(defaultMap="DAC38RF8x.json")


struct = {                          \
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


dac.readStruct(struct)

dac.writeStruct(struct)


FTDISPI.printStruct(struct)


FTDISPI.printStruct(dac.currentState())
