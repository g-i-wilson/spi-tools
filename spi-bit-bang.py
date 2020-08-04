from pyftdi.gpio import GpioSyncController
import time

class BitBangSPI:
	def __init__(self, device, SCLK, MOSI, MISO, CS, defaultDirection=0xBB, defaultState=0x00):
		self.SCLK = SCLK
		self.MOSI = MOSI
		self.MISO = MISO
		self.CS = CS
		self.defaultDirection = defaultDirection
		self.defaultState = defaultState
		self.txArray = bytearray()
		self.txArray.append(self.defaultState | self.CS)
		self.directionArray = bytearray()
		self.directionArray.append(self.defaultDirection)
		self.rxArray = bytearray()
	def writeDelay(self, d, directionMask=0x00):
		for i in range(d):
			self.txArray.append(self.txArray[-1])
			self.directionArray.append(self.directionArray[-1] & ~directionMask)
	def clockLow(self, directionMask=0x00):
		self.txArray.append( self.txArray[-1] & ~self.SCLK )
		self.directionArray.append(self.directionArray[-1] & ~directionMask)
	def clockLowdataHigh(self, directionMask=0x00):
		self.txArray.append( (self.txArray[-1] & ~self.SCLK) | self.MOSI )
		self.directionArray.append(self.directionArray[-1] & ~directionMask)
	def clockLowdataLow(self, directionMask=0x00):
		self.txArray.append( (self.txArray[-1] & ~self.SCLK) & ~self.MOSI )
		self.directionArray.append(self.directionArray[-1] & ~directionMask)
	def clockHigh(self, directionMask=0x00):
		self.txArray.append( self.txArray[-1] | self.SCLK )
		self.directionArray.append(self.directionArray[-1] & ~directionMask)
	def csLow(self, directionMask=0x00):
		self.txArray.append( self.txArray[-1] & ~self.CS )
		self.directionArray.append(self.directionArray[-1] & ~directionMask)
	def csHigh(self, directionMask=0x00):
		self.txArray.append( self.txArray[-1] | self.CS )
		self.directionArray.append(self.directionArray[-1] & ~directionMask)
	def writeByte(self, aByte, directionMask=0x00):
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
		gpio = GpioSyncController(device, self.direction, frequency)
		gpio.configure()
		self.rxArray = gpio.exchange( self.txArray );
		gpio.close()
	def transmitAsync(self, halfPeriod=0.005):
		gpio = GpioAsyncController()
		gpio.configure(device, self.directionArray[0])
		for i in range(len(self.txArray)):
			if (self.directionArray[i] != self.directionArray[i-1]):
				gpio.configure(device, self.directionArray[i])
			# all output set high, apply direction mask
			gpio.write(self.txArray[i] & gpio.direction)
			time.sleep(halfPeriod)
		# all output forced to high, writing to input pins is illegal
		gpio.write(0xFF)  # raises an IOError
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


def readData(bitBangArray, clockMask, mosiMask, misoMask, directionArray=bytearray(), debug=1):
	mosiArray = bytearray()
	misoArray = bytearray()
	bitPlace = 7
	mosiByte = 0x00
	misoByte = 0x00
	for a in range(len(bitBangArray)):
		if debug:
			print("output= ", end='')
			printByte(bitBangArray[a])
			print(", direction= ", end='')
			printByte(directionArray[a])
		if (not (bitBangArray[a-1] & clockMask) and (bitBangArray[a] & clockMask)): # rising edge
			if debug: print(", rising edge, bitPlace=" + str(bitPlace), end='')
			if (bitBangArray[a] & mosiMask):
				if debug: print(", mosi=1", end='')
				mosiByte += (1 << bitPlace)
			if (bitBangArray[a] & misoMask): # data=1
				if debug: print(", miso=1", end='')
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
	
	
def formatData(txMOSI, txMISO, rxMOSI, rxMISO): #must all be same length
	print(    "TX:         |  RX:")
	print(    "MOSI  MISO  |  MOSI  MISO")
	for i in range(len(txMOSI)):
		print("0x{:02x}".format(txMOSI[i])+"  "+"0x{:02x}".format(txMISO[i])+"  |  "+"0x{:02x}".format(rxMOSI[i])+"  "+"0x{:02x}".format(rxMISO[i]))
	print()


def spiTransaction(writeList, testing=1):
	sckMask = 0x10
	sdioMask = 0x20
	sdoMask = 0x40
	csMask = 0x80
	txBytes = BitBangSPI('ftdi:///2', sckMask, sdioMask, sdoMask, csMask) 

	### Convert writeList into txBytes array (bit-bang) ###
	for aWrite in writeList:
		txBytes.writeDelay(4)
		txBytes.clockLow()
		txBytes.csLow()
		# SPI control and address bytes
		txBytes.writeByte(aWrite[0])
		txBytes.writeByte(aWrite[1])
		# Data byte
		if (aWrite[0] & 0x80):
			txBytes.writeByte(aWrite[2], directionMask=0x20)
		else:
			txBytes.writeByte(aWrite[2])
		txBytes.csHigh()
		txBytes.clockLow()
		txBytes.writeDelay(4)
		### SPI send and receive ###
	if not testing:
		#txBytes.transmitSync()
		txBytes.transmitAsync
	#print("directionArray:")
	#printBin(txBytes.getDirectionArray())
	return [\
		readData(txBytes.getTxArray(), sckMask, sdioMask, sdoMask, directionArray=txBytes.getDirectionArray()),\
		readData(txBytes.getRxArray(), sckMask, sdioMask, sdoMask, directionArray=txBytes.getDirectionArray())\
		]



writeList = [[0x00,0x00,0x10],\
			[0x01,0x38,0x40],\
			[0x01,0x3F,0x00],\
			[0x01,0x40,0xF0],\
			[0x01,0x47,0x00],\
			[0x01,0x73,0x60]]
			
readList = [[0x00,0x00,0x10],\
			[0x81,0x38,0x00],\
			[0x81,0x3F,0x00],\
			[0x81,0x40,0x00],\
			[0x81,0x47,0x00],\
			[0x81,0x73,0x00]]

#writeList = [[0xCC,0xCC,0xCC],[0xAA,0xAA,0xAA]]

#for i in range(100):
writeResults = spiTransaction(writeList, 0); # write

#readResults = spiTransaction(readList, 0); # read

#formatData(writeResults[0][0], writeResults[0][1], writeResults[1][0], writeResults[1][1])
#formatData(readResults[0][0], readResults[0][1], readResults[1][0], readResults[1][1])
	#time.sleep(.5)
	









	