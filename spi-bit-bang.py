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




for i in range(100):
	spiTransaction(write4wire); # write
	spiTransaction(read4wire); # read
	time.sleep(.1)
	









	