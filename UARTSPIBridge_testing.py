import FTDISPI

bridge = FTDISPI.UARTSPIBridge( port="/dev/ttyUSB0" )

print( bridge.read([0x55], 1) )
