from pyftdi.spi import SpiController
import time
import sys




# data structure format: [ [ADDR, upper_byte, lower_byte], [...], ... ]
defaultMap =    [ \
                [0x00, 0x58, 0x03], # RESET_CONFIG Chip Reset and Configuration 8.5.1 \
                [0x01, 0x18, 0x00], # IO_CONFIG IO Configuration 8.5.2 \
                [0x02, 0xFF, 0xFF], # ALM_SD_MASK Lane Signal Detect Alarm Mask 8.5.3 \
                [0x03, 0xFF, 0xFF], # ALM_CLK_MASK Clock Alarms Mask 8.5.4 \
                [0x04, 0x00, 0x00], # variable (1) ALM_SD_DET SERDES Loss of Signal Detection Alarms 8.5.5 \
                [0x05, 0x00, 0x00], # variable (1) ALM_SYSREF_DET SYSREF Alignment Circuit Alarms 8.5.6 \
                [0x06, 0x00, 0x00], # variable TEMP_PLLVOLT Temperature Sensor and PLL Loop Voltage 8.5.7 \
                [0x09, 0x00, 0x00], # PAGE_SET Page Set  \
                [0x78, 0x00, 0x00], # SYSREF_ALIGN_R SYSERF Align to r1 and r3 Count 8.5.9 \
                [0x79, 0x00, 0x00], # SYSREF12_CNT SYSREF Phase Count 1 and 2 8.5.10 \
                [0x7A, 0x00, 0x00], # SYSREF34_CNT SYSREF Phase Count 3 and 4 \
                [0x7F, 0x00, 0x09], # VENDOR_VER Vendor ID and Chip Version \
                [0x0A, 0x02, 0xB0], # MULTIDUC_CFG1 Multi-DUC Configuration (PAP, Interpolation)  \
                [0x0C, 0x24, 0x02], # MULTIDUC_CFG2 Multi-DUC Configuration (Mixers) 8.5.14 \
                [0x0D, 0x80, 0x00], # JESD_FIFO JESD FIFO Control 8.5.15 \
                [0x0E, 0x00, 0xFF], # ALM_MASK1 Alarm Mask 1 8.5.16 \
                [0x0F, 0xFF, 0xFF], # ALM_MASK2 Alarm Mask 2 8.5.17 \
                [0x10, 0xFF, 0xFF], # ALM_MASK3 Alarm Mask 3 8.5.18 \
                [0x11, 0xFF, 0xFF], # ALM_MASK4 Alarm Mask 4 8.5.19 \
                [0x12, 0x00, 0x00], # JESD_LN_SKEW JESD Lane Skew 8.5.20 \
                [0x17, 0x00, 0x00], # CMIX CMIX Configuration \
                [0x19, 0x00, 0x00], # OUTSUM Output Summation and Delay \
                [0x1C, 0x00, 0x00], # PHASE_NCOAB Phase offset for AB path NCO 8.5.23 \
                [0x1D, 0x00, 0x00], # PHASE_NCOCD Phase offset for CD path NCO 8.5.24 \
                [0x1E, 0x00, 0x00], # 0x1E-0x20 0x0000 FREQ_NCOAB Frequency for AB path NCO 8.5.25 \
                [0x1F, 0x00, 0x00], \
                [0x20, 0x00, 0x00], \
                [0x21, 0x00, 0x00], # 0x21-0x23 0x0000 FREQ_NCOCD Frequency for CD path NCO 8.5.26 \
                [0x22, 0x00, 0x00], \
                [0x23, 0x00, 0x00], \
                [0x24, 0x00, 0x10], # SYSREF_CLKDIV SYSREF Use for Clock Divider 8.5.27 \
                [0x25, 0x77, 0x00], # SERDES_CLK Serdes Clock Control 8.5.28 \
                [0x27, 0x11, 0x44], # SYNCSEL1 Sync Source Selection 8.5.29 \
                [0x28, 0x00, 0x00], # SYNCSEL2 Sync Source Selection 8.5.30 \
                [0x29, 0x00, 0x00], # PAP_GAIN_AB PAP path AB Gain Attenuation Step 8.5.31 \
                [0x2A, 0x00, 0x00], # PAP_WAIT_AB PAP path AB Wait Time at Gain = 0 8.5.32 \
                [0x2B, 0x00, 0x00], # PAP_GAIN_CD PAP path CD Gain Attenuation Step 8.5.33 \
                [0x2C, 0x00, 0x00], # PAP_WAIT_CD PAP path CD Wait Time at Gain = 0 8.5.34 \
                [0x2D, 0x1F, 0xFF], # PAP_CFG_AB PAP path AB Configuration 8.5.35 \
                [0x2E, 0x1F, 0xFF], # PAP_CFG_CD PAP path CD Configuration 8.5.36 \
                [0x2F, 0x00, 0x00], # SPIDAC_TEST1 Configuration for DAC SPI Constant 8.5.37 \
                [0x30, 0x00, 0x00], # SPIDAC_TEST2 DAC SPI Constant 8.5.38 \
                [0x32, 0x04, 0x00], # GAINAB Gain for path AB 8.5.39 \
                [0x33, 0x04, 0x00], # GAINCD Gain for path CD 8.5.40 \
                [0x41, 0x00, 0x00], # JESD_ERR_CNT JESD Error Counter \
                [0x46, 0x00, 0x44], # JESD_ID1 JESD ID 1 8.5.42 \
                [0x47, 0x19, 0x0A], # JESD_ID2 JESD ID 2 8.5.43 \
                [0x48, 0x31, 0xC3], # JESD_ID3 JESD ID 3 and Subclass 8.5.44 \
                [0x4A, 0x00, 0x03], # JESD_LN_EN JESD Lane Enable 8.5.45 \
                [0x4B, 0x13, 0x00], # JESD_RBD_F JESD RBD Buffer and Frame Octets 8.5.46 \
                [0x4C, 0x13, 0x03], # JESD_K_L JESD K and L Parameters 8.5.47 \
                [0x4D, 0x01, 0x00], # JESD_M_S JESD M and S Parameters 8.5.48 \
                [0x4E, 0x0F, 0x4F], # JESD_N_HD_SCR JESD N, HD and SCR Parameters 8.5.49 \
                [0x4F, 0x1C, 0xC1], # JESD_MATCH JESD Character Match and Other 8.5.50 \
                [0x50, 0x00, 0x00], # JESD_LINK_CFG JESD Link Configuration Data 8.5.51 \
                [0x51, 0x00, 0xFF], # JESD_SYNC_REQ JESD Sync Request 8.5.52 \
                [0x52, 0x00, 0xFF], # JESD_ERR_OUT JESD Error Output 8.5.53 \
                [0x53, 0x01, 0x00], # JESD_ILA_CFG1 JESD Configuration Value used for ILA \
                [0x54, 0x8E, 0x60], # JESD_ILA_CFG2 JESD Configuration Value used for ILA \
                [0x5C, 0x00, 0x01], # JESD_SYSR_MODE JESD SYSREF Mode \
                [0x5F, 0x01, 0x23], # JESD_CROSSBAR1 JESD Crossbar Configuration 1 8.5.57 \
                [0x60, 0x45, 0x67], # JESD_CROSSBAR2 JESD Crossbar Configuration 2 8.5.58 \
                [0x64, 0x00, 0x00], # JESD_ALM_L0 JESD Alarms for Lane 0 8.5.59 \
                [0x65, 0x00, 0x00], # JESD_ ALM_L1 JESD Alarms for Lane 1 8.5.60 \
                [0x66, 0x00, 0x00], # JESD_ ALM_L2 JESD Alarms for Lane 2 8.5.61 \
                [0x67, 0x00, 0x00], # JESD_ALM_L3 JESD Alarms for Lane 3 8.5.62 \
                [0x68, 0x00, 0x00], # JESD_ALM_L4 JESD Alarms for Lane 4 8.5.63 \
                [0x69, 0x00, 0x00], # JESD_ALM_L5 JESD Alarms for Lane 5 8.5.64 \
                [0x6A, 0x00, 0x00], # JESD_ALM_L6 JESD Alarms for Lane 6 8.5.65 \
                [0x6B, 0x00, 0x00], # JESD_ALM_L7 JESD Alarms for Lane 7 8.5.66 \
                [0x6C, 0x00, 0x00], # ALM_SYSREF_PAP SYSREF and PAP Alarms 8.5.67 \
                [0x6D, 0x00, 0x00], # ALM_CLKDIV1 Clock Divider Alarms 1 8.5.68 \
                [0x0A, 0xFC, 0x03], # CLK_CONFIG Clock Configuration 8.5.69 \
                [0x0B, 0x00, 0x22], # SLEEP_CONFIG Sleep Configuration 8.5.70 \
                [0x0C, 0xA0, 0x02], # CLK_OUT Divided Output Clock Configuration 8.5.71 \
                [0x0D, 0xF0, 0x00], # DACFS DAC Fullscale Current 8.5.72 \
                [0x10, 0x00, 0x00], # LCMGEN Internal sysref generator 8.5.73 \
                [0x11, 0x00, 0x00], # LCMGEN_DIV Counter for internal sysref generator 8.5.74 \
                [0x12, 0x00, 0x00], # LCMGEN_SPISYSREF SPI SYSREF for internal sysref generator 8.5.75 \
                [0x1B, 0x00, 0x00], # DTEST Digital Test Signals \
                [0x23, 0xFF, 0xFF], # SLEEP_CNTL Sleep Pin Control 8.5.77 \
                [0x24, 0x10, 0x00], # SYSR_CAPTURE SYSREF Capture Circuit Control 8.5.78 \
                [0x31, 0x02, 0x00], # CLK_PLL_CFG Clock Input and PLL Configuration 8.5.79 \
                [0x32, 0x03, 0x08], # PLL_CONFIG1 PLL Configuration 1 8.5.80 \
                [0x33, 0x40, 0x18], # PLL_CONFIG2 PLL Configuration 2 8.5.81 \
                [0x34, 0x00, 0x00], # LVDS_CONFIG LVDS Output Configuration 8.5.82 \
                [0x35, 0x00, 0x18], # PLL_FDIV Fuse farm clock divider 8.5.83 \
                [0x3B, 0x18, 0x02], # SRDS_CLK_CFG Serdes Clock Configuration 8.5.84 \
                [0x3C, 0x82, 0x28], # SRDS_PLL_CFG Serdes PLL Configuration 8.5.85 \
                [0x3D, 0x00, 0x88], # SRDS_CFG1 Serdes Configuration 1 8.5.86 \
                [0x3E, 0x09, 0x09], # SRDS_CFG2 Serdes Configuration 2 8.5.87 \
                [0x3F, 0x00, 0x00], # SRDS_POL Serdes Polarity Control 8.5.88 \
                [0x76, 0x00, 0x00], # SYNCBOUT JESD204B SYNCB Output \
                                 ]


def printByte(aByte):
	for aBit in range(8):
		if ((aByte >> (7-aBit)) & 0x01):
			print("1 ", end='')
		else:
			print("_ ", end='')


def printBytes(aByteArray):
	for aByte in aByteArray:
		printByte(aByte)
		print()


def printHex(aByteArray):
	for aByte in aByteArray:
		print(hex(aByte))


def printReg(addrByte, twoByteArray):
	print(hex(addrByte), end=': ')
	print(hex(twoByteArray[0]), end=', ')
	print(hex(twoByteArray[1]), end=' ')
	# print(": ", end='')
	printByte(twoByteArray[0])
	print("   ", end='')
	printByte(twoByteArray[1])
	print()




# Instantiate a SPI controller
spi = SpiController()

# Configure the first interface (IF/1) of the FTDI device as a SPI master
spi.configure('ftdi:///2')

# Get a port to a SPI slave w/ /CS on A*BUS3 and SPI mode 0 @ 12MHz
slave = spi.get_port(cs=0, freq=1E6, mode=0)

# Request the JEDEC ID from the SPI slave
# jedec_id = slave.exchange([0x9f], 3)
def formatBytes(bytes, orMasks):
    newBytes = bytearray();
    for i in range(len(bytes)):
        newBytes.append(bytes[i] | orMasks[i])
    return newBytes


def writeReg(reg, upper=0x00, lower=0x00, cs_start=True, cs_stop=True):
    return slave.exchange( \
        out = [ \
            reg, \
            upper, \
            lower \
        ], \
        readlen=0, \
        start=cs_start, \
        stop=cs_stop, \
        duplex=False, \
        droptail=0 \
    )

def readReg(reg, cs_start=True, cs_stop=True):
    return slave.exchange( \
        out=[ (reg | 0x80) ], \
        readlen=2, \
        start=cs_start, \
        stop=cs_stop, \
        duplex=False, \
        droptail=0 \
    )


def bitOn(reg, upperBitMask, lowerBitMask):
	currentState = readReg(reg)
	writeReg(reg, currentState[0] | upperBitMask, currentState[1] | lowerBitMask)
	return readReg(reg)

def bitOff(reg, upperBitMask, lowerBitMask):
	currentState = readReg(reg)
	writeReg(reg, currentState[0] & ~upperBitMask, currentState[1] & ~lowerBitMask)
	return readReg(reg)


# writeReg( defaultMap[0], upperMask=0x80, lowerMask=0x00, start=True, stop=False )
# writeReg( defaultMap[1], upperMask=0x00, lowerMask=0x08, start=True, stop=False )
# printBytes( formatBytes([0x01, 0x18, 0x00],[0x80, 0x00, 0x00]) )
# printHex( readReg( 0x81 ) )
printReg( 0x03, bitOn( 0x03, 0x00, 0x04 ) )
printReg( 0x03, bitOff( 0x03, 0x00, 0x04 ) )

for aReg in defaultMap:
	printReg( aReg[0], readReg( aReg[0], cs_start=True, cs_stop=True ) )
# printHex( slave.exchange([0x81,0x18,0x80],readlen=2))

# dacReg( [0x01, 0x18, 0x00], lowerMask=0x08, read=False, start=True, stop=False )
# print()
# for aReg in defaultMap:
#     printReg( dacReg( aReg, start=False, stop=False ) )
# print()
# dacReg( [0x01, 0x18, 0x00], start=False, stop=True )
