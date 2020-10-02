import FTDISPI
import sys

bridge = FTDISPI.UARTSPIBridge( port=sys.argv[1] )

print( bridge.read([ int(sys.argv[2],16) ], 1) )
