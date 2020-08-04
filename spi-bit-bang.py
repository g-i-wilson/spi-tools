from pyftdi.gpio import GpioSyncController
from pyftdi.gpio import GpioAsyncController
import time

class BitBangSPI:
	def __init__(self, device, SCLK, MOSI, MISO, CS, defaultDirection, defaultState):
		self.device = device
		self.SCLK = SCLK
		self.MOSI = MOSI
		self.MISO = MISO
		self.CS = CS
		self.defaultDirection = defaultDirection
		self.defaultState = defaultState
		self.txArray = bytearray()
		self.txArray.append((self.defaultState | self.CS) & defaultDirection)
		self.directionArray = bytearray()
		self.directionArray.append(self.defaultDirection)
		self.rxArray = bytearray()
	def insertDelay(self, d, directionMask=0xff):
		for i in range(d):
			self.txArray.append(self.txArray[-1])
			self.directionArray.append(self.defaultDirection & directionMask)
	def clockLow(self, directionMask=0xff):
		self.txArray.append( self.txArray[-1] & ~self.SCLK )
		self.directionArray.append(self.defaultDirection & directionMask)
	def clockLowdataHigh(self, directionMask=0xff):
		self.txArray.append( (self.txArray[-1] & ~self.SCLK) | self.MOSI )
		self.directionArray.append(self.defaultDirection & directionMask)
	def clockLowdataLow(self, directionMask=0xff):
		self.txArray.append( (self.txArray[-1] & ~self.SCLK) & ~self.MOSI )
		self.directionArray.append(self.defaultDirection & directionMask)
	def clockHigh(self, directionMask=0xff):
		self.txArray.append( self.txArray[-1] | self.SCLK )
		self.directionArray.append(self.defaultDirection & directionMask)
	def csLow(self, directionMask=0xff):
		self.txArray.append( self.txArray[-1] & ~self.CS )
		self.directionArray.append(self.defaultDirection & directionMask)
	def csHigh(self, directionMask=0xff):
		self.txArray.append( self.txArray[-1] | self.CS )
		self.directionArray.append(self.defaultDirection & directionMask)
	def writeByte(self, aByte, directionMask=0xff):
		for i in range(8):
			shiftPlaces = 7-i # MSB first "big endian"
			# clock falling edge and data transition
			if ((aByte >> shiftPlaces) & 0x01):
				self.clockLowdataHigh(directionMask)
			else:
				self.clockLowdataLow(directionMask)
			# clock rising edge
			self.clockHigh(directionMask)
	def getTxArray(self):
		return self.txArray
	def transmitSync(self, frequency=1e3):
		gpio = GpioSyncController()
		gpio.configure(self.device, self.directionArray[0], frequency=frequency)
		self.rxArray = gpio.exchange( self.txArray );
		gpio.close()
	def transmitAsync(self, halfPeriod=0.005):
		gpio = GpioAsyncController()
		gpio.configure(self.device, self.directionArray[0])
		for i in range(len(self.txArray)):
			if (self.directionArray[i] != self.directionArray[i-1]):
				time.sleep(halfPeriod)
				gpio.close()
				gpio = GpioAsyncController()
				gpio.configure(self.device, self.directionArray[i])
				time.sleep(halfPeriod)
				#print("new direction: "+hex(self.directionArray[i]))
			# read the state of the port
			self.rxArray.append( gpio.read() )
			#print("read: "+hex(self.rxArray[-1]))
			# write to the outputs (0 is OK to write to inputs)
			gpio.write(self.txArray[i])
			#print("write: "+hex(self.txArray[i]))
			# wait half a clock cycle
			time.sleep(halfPeriod)
		gpio.close()
	def getRxArray(self):
		return self.rxArray
	def getDirectionArray(self):
		return self.directionArray
			
			
			
			
		
def printByte(aByte):
	for aBit in range(8):
		if ((aByte >> (7-aBit)) & 0x01):
			print("1 ", end='')
		else:
			print("_ ", end='')		
		
		
def printBin(bitBangArray):
	for aByte in bitBangArray:
		printByte(aByte)
		print()

def printHex(bitBangArray):
	for aByte in bitBangArray:
		print(hex(aByte))


def readBitBang(bitBangArray, clockMask, mosiMask, misoMask, directionArray=bytearray(), debug=0):
	mosiArray = bytearray()
	misoArray = bytearray()
	bitPlace = 7
	mosiByte = 0x00
	misoByte = 0x00
	for a in range(len(bitBangArray)):
		if debug:
			print("state= ", end='')
			printByte(bitBangArray[a])
			print(", direction= ", end='')
			printByte(directionArray[a])
		if (not (bitBangArray[a-1] & clockMask) and (bitBangArray[a] & clockMask)): # rising edge
			if debug: print(", rising edge, bitPlace=" + str(bitPlace), end='')
			if (bitBangArray[a] & mosiMask):
				if debug: print(", master=1", end='')
				mosiByte += (1 << bitPlace)
			if (bitBangArray[a] & misoMask): # data=1
				if debug: print(", slave=1", end='')
				misoByte += (1 << bitPlace)
			bitPlace -= 1
		if bitPlace < 0:
			mosiArray.append(mosiByte)
			misoArray.append(misoByte)
			if debug:
				print(", mosiByte="+hex(mosiByte)+", misoByte="+hex(misoByte), end='')
			mosiByte = 0x00
			misoByte = 0x00
			bitPlace = 7
		if debug:
			print()
	return [mosiArray, misoArray]
	
	
def displayData(bb): #must all be same length
	tx = readBitBang( bb.getTxArray(), bb.SCLK, bb.MOSI, bb.MISO, bb.getDirectionArray() )
	rx = readBitBang( bb.getRxArray(), bb.SCLK, bb.MOSI, bb.MISO, bb.getDirectionArray() )
	print(    "TX:         |  RX:")
	print(    "MOSI  MISO  |  MOSI  MISO")
	for i in range(len(tx[0])):
		print( \
			"0x{:02x}".format(tx[0][i])+ \
			"  "+"0x{:02x}".format(tx[1][i])+ \
			"  |  "+"0x{:02x}".format(rx[0][i])+ \
			"  "+"0x{:02x}".format(rx[1][i]) \
			)
	print()


def spiTransaction(transactionList):
	sckMask = 0x10
	sdioMask = 0x20
	sdoMask = 0x40
	csMask = 0x80
	txBytes = BitBangSPI('ftdi:///2', sckMask, sdioMask, sdoMask, csMask, defaultDirection=0xBB, defaultState=0x88) 

	### Convert transactionList into txBytes array (bit-bang) ###
	for aTransaction in transactionList:
		txBytes.insertDelay(4)
		txBytes.clockLow()
		txBytes.csLow()
		# SPI control and address bytes
		txBytes.writeByte(aTransaction[0])
		txBytes.writeByte(aTransaction[1])
		# Data byte
		txBytes.writeByte(aTransaction[2])
#		if (aTransaction[0] & 0x80):
#			txBytes.writeByte(aTransaction[2], directionMask=(~0x20)) # reconfigure pin 0x20 as input
#		else:
#			txBytes.writeByte(aTransaction[2])
		txBytes.csHigh()
		txBytes.clockLow()
		txBytes.insertDelay(4)
	### SPI send and receive ###
	txBytes.transmitSync(frequency=10000)
	#txBytes.transmitAsync()
	displayData( txBytes );




write4wire =	[[0x00,0x00,0x10],\
				[0x01,0x38,0x40],\
				[0x01,0x3F,0x00],\
				[0x01,0x40,0xF0],\
				[0x01,0x47,0x00],\
				[0x01,0x4A,0x33],\
				[0x01,0x73,0x60]]


read4wire =		[[0x00,0x00,0x10],\
				[0x81,0x38,0x00],\
				[0x81,0x3F,0x00],\
				[0x81,0x40,0x00],\
				[0x81,0x47,0x00],\
				[0x01,0x4A,0x00],\
				[0x81,0x73,0x00]]


readAll4wire = 	[[0x00,0x00,0x10],\
				[0x80,0x02,0x00],\
				[0x80,0x03,0x00],\
				[0x80,0x04,0x00],\
				[0x80,0x05,0x00],\
				[0x80,0x06,0x00],\
				[0x80,0x0C,0x00],\
				[0x80,0x0D,0x00],\
				[0x81,0x00,0x00],\
				[0x81,0x01,0x00],\
				[0x81,0x03,0x00],\
				[0x81,0x04,0x00],\
				[0x81,0x05,0x00],\
				[0x81,0x06,0x00],\
				[0x81,0x07,0x00],\
				[0x81,0x08,0x00],\
				[0x81,0x09,0x00],\
				[0x81,0x0B,0x00],\
				[0x81,0x0C,0x00],\
				[0x81,0x0D,0x00],\
				[0x81,0x0E,0x00],\
				[0x81,0x0F,0x00],\
				[0x81,0x10,0x00],\
				[0x81,0x11,0x00],\
				[0x81,0x13,0x00],\
				[0x81,0x14,0x00],\
				[0x81,0x15,0x00],\
				[0x81,0x16,0x00],\
				[0x81,0x17,0x00],\
				[0x81,0x18,0x00],\
				[0x81,0x19,0x00],\
				[0x81,0x1B,0x00],\
				[0x81,0x1C,0x00],\
				[0x81,0x1D,0x00],\
				[0x81,0x1E,0x00],\
				[0x81,0x1F,0x00],\
				[0x81,0x20,0x00],\
				[0x81,0x21,0x00],\
				[0x81,0x23,0x00],\
				[0x81,0x24,0x00],\
				[0x81,0x25,0x00],\
				[0x81,0x26,0x00],\
				[0x81,0x27,0x00],\
				[0x81,0x28,0x00],\
				[0x81,0x29,0x00],\
				[0x81,0x2B,0x00],\
				[0x81,0x2C,0x00],\
				[0x81,0x2D,0x00],\
				[0x81,0x2E,0x00],\
				[0x81,0x2F,0x00],\
				[0x81,0x30,0x00],\
				[0x81,0x31,0x00],\
				[0x81,0x33,0x00],\
				[0x81,0x34,0x00],\
				[0x81,0x35,0x00],\
				[0x81,0x36,0x00],\
				[0x81,0x37,0x00],\
				[0x81,0x38,0x00],\
				[0x81,0x39,0x00],\
				[0x81,0x3A,0x00],\
				[0x81,0x3B,0x00],\
				[0x81,0x3C,0x00],\
				[0x81,0x3D,0x00],\
				[0x81,0x3E,0x00],\
				[0x81,0x3F,0x00],\
				[0x81,0x40,0x00],\
				[0x81,0x41,0x00],\
				[0x81,0x42,0x00],\
				[0x81,0x43,0x00],\
				[0x81,0x44,0x00],\
				[0x81,0x45,0x00],\
				[0x81,0x46,0x00],\
				[0x81,0x47,0x00],\
				[0x81,0x48,0x00],\
				[0x81,0x49,0x00],\
				[0x81,0x4A,0x00],\
				[0x81,0x4B,0x00],\
				[0x81,0x4C,0x00],\
				[0x81,0x4D,0x00],\
				[0x81,0x4E,0x00],\
				[0x81,0x4F,0x00],\
				[0x81,0x50,0x00],\
				[0x81,0x51,0x00],\
				[0x81,0x52,0x00],\
				[0x81,0x53,0x00],\
				[0x81,0x54,0x00],\
				[0x81,0x55,0x00],\
				[0x81,0x56,0x00],\
				[0x81,0x57,0x00],\
				[0x81,0x58,0x00],\
				[0x81,0x59,0x00],\
				[0x81,0x5A,0x00],\
				[0x81,0x5B,0x00],\
				[0x81,0x5C,0x00],\
				[0x81,0x5D,0x00],\
				[0x81,0x5E,0x00],\
				[0x81,0x5F,0x00],\
				[0x81,0x60,0x00],\
				[0x81,0x61,0x00],\
				[0x81,0x62,0x00],\
				[0x81,0x63,0x00],\
				[0x81,0x64,0x00],\
				[0x81,0x65,0x00],\
				[0x81,0x66,0x00],\
				[0x81,0x67,0x00],\
				[0x81,0x68,0x00],\
				[0x81,0x69,0x00],\
				[0x81,0x6A,0x00],\
				[0x81,0x6B,0x00],\
				[0x81,0x6C,0x00],\
				[0x81,0x6D,0x00],\
				[0x81,0x6E,0x00],\
				[0x81,0x71,0x00],\
				[0x81,0x72,0x00],\
				[0x81,0x73,0x00],\
				[0x81,0x74,0x00],\
				[0x81,0x7C,0x00],\
				[0x81,0x7D,0x00],\
				[0x81,0x82,0x00],\
				[0x81,0x83,0x00],\
				[0x81,0x84,0x00],\
				[0x81,0x85,0x00],\
				[0x81,0x88,0x00],\
				[0x9F,0xFD,0x00],\
				[0x9F,0xFE,0x00],\
				[0x9F,0xFF,0x00]]



write3wire =	[[0x00,0x00,0x80],\
				[0x01,0x38,0x40],\
				[0x01,0x3F,0x00],\
				[0x01,0x40,0xF0],\
				[0x01,0x47,0x00],\
				[0x01,0x73,0x60]]


read3wire =		[[0x00,0x00,0x80],\
				[0x81,0x38,0x00],\
				[0x81,0x3F,0x00],\
				[0x81,0x40,0x00],\
				[0x81,0x47,0x00],\
				[0x81,0x73,0x00]]




#for i in range(100):
spiTransaction(write4wire); # write
spiTransaction(readAll4wire); # read
#	time.sleep(.1)
	









	