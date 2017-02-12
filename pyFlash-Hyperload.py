#!/usr/bin/env python
# SJSU - AV #

########
# CHANGELOG:
# 2016-02-15 : Working Skeleton for Flashing a Hex file to SJOne comeplete!
#

import serial
import string
import os
import time
import struct
import binascii
import math
import serial.serialutil
import logging
import sys
import getopt
from intelhex import IntelHex

###############################################################################
################# CONFIGURATION FOR pyFlash - Hyperload ######################
###############################################################################
sDeviceFile = "/dev/tty.usbserial-A503JOHW-D"   # Device File Path
sDeviceBaud = 1000000          # Suitable Device Baud Rate
sHexFilePath = "/Users/atkvo/Workspace/eclipse/test/Debug/test.hex-D"
sGenerateBinary = "y"  # "y" - Yes | "n" - No
###############################################################################

#### LOGGING OPTIONS ####
PYFLASH_DEBUG_LOG = "no"  # "yes" - Debug Version. "no" - Release Version
#########################


if PYFLASH_DEBUG_LOG == "yes":
    PYFLASH_BUILD_LEVEL = "DEBUG"
else:
    PYFLASH_BUILD_LEVEL = "RELEASE"

if PYFLASH_BUILD_LEVEL == "DEBUG":
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
else:
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)


# Things to Do:
# 1. Display Platform Information                               [DONE]
# 2. Enable a Debug/Release Switch                              [DONE]
# 3. Create ~/.pyFlash and store last used options for Flashing [PEND]
# 4. Handle Exceptions                                          [PEND]
# 5. Ensure packing is done based on Endianness                 [PEND]
# 6. Re-write program with classes using this as the backbone.  [PEND]
# 7. Incorporate design decisions keeping the GUI in mind       [PEND]

# Issues Faced
# 1. Handling Bytes were hard - Use bytearray for most of the IO related
#       functions. Difference between bytes and bytearray
#       is that the latter is mutable.
#    Bytes are types that are not mutable.
#    Any changes done on them will cause a new alloc + concat and reassigning.

# Global Defines

ApplicationVersion = "1.0"
ToolName = "pyFLASH - HYPERLOAD"
ToolInfo = "Flashing Tool for SJOne"
BaudList = [4800, 9600, 19200, 38400]
ControlWordList = b'\x80\xf8\xfe\xff'
SpecialChar = {'Dollar': '$', 'OK': '!', 'NextLine': '\n', 'STAR': '*'}
sCPUSpeed = 48000000
sInitialDeviceBaud = 38400

ByteReference = b'\xff\x55\xaa'


# Common Util Functions
def printIntroMessage():
    print "#######################"
    print " ", ToolName
    print ToolInfo
    print "#######################"
    print "Version    : ", ApplicationVersion
    print "Build Type : ", PYFLASH_BUILD_LEVEL
    print "#######################"

    return


def printBytes(mymsg):

    print "Type info = " + (str)(type(mymsg))

    if (type(mymsg) == bytes) or (type(mymsg) == bytearray):
        for x in mymsg:
            print "0x" + '{:x}'.format(x),

        print ""
        print "Total Elements = " + (str)(len(mymsg))

    elif (type(mymsg) == str):
        printBytes(bytearray(mymsg))

    elif type(mymsg) == int:
        print "0x" + '{:x}'.format(mymsg),

    else:
        print mymsg

    return


def getBoardParameters(descString):
    boardParametersDict = {'Board': '',
                           'BlockSize': '',
                           'BootloaderSize': '',
                           'FlashSize': ''}

    # Parsing String to obtain required Board Parameters
    boardParametersList = descString.split(':')

    boardParametersDict['Board'] = boardParametersList[0]
    boardParametersDict['BlockSize'] = boardParametersList[1]
    boardParametersDict['BootloaderSize'] = (int(boardParametersList[2]) * 2)
    boardParametersDict['FlashSize'] = boardParametersList[3]

    print "\n***** Board Information ********"
    print "Board              = " + (str)(boardParametersDict['Board'])
    print "Block (Chunk) Size = " + (str)(boardParametersDict['BlockSize']) + " bytes"
    print "Bootloader Size    = " + (str)(boardParametersDict['BootloaderSize']) + " bytes"
    print "Flash Size         = " + (str)(boardParametersDict['FlashSize']) + " KBytes"
    print "*********************************\n"

    return boardParametersDict


def printContent(lContent):

    logging.debug("--------------------")
    count = 0
    totalCount = 0
    for x in lContent:
        print '{:2x}'.format(x),
        if count >= 10:
            print "\n"
            count = 0
        else:
            count = count + 1
        totalCount = totalCount + 1

    logging.debug("\n--------------------")
    logging.debug("Total Count = ", totalCount)
    logging.debug("--------------------")

    return


def getControlWord(baudRate, cpuSpeed):
    # TODO : Currently using known values. Replace with actual formula
    logging.debug("Retrieving Control Word")

    controlWord = ((cpuSpeed / (baudRate * 16)) - 1)

    return controlWord


def getPageContent(bArray, blkCount, pageSize):

    # startOffset = blkCount * pageSize         # this variable is never used
    # endOffset = (startOffset + pageSize - 1)  # this variable is never used

    # print "Page Start = ", startOffset, " | Page End = ", str(endOffset)

    lPageContent = bytearray(pageSize)
    for x in range(0, pageSize):
        lPageContent[x] = bArray[x + (blkCount * pageSize)]

    # print "Length of x = ", x

    if x != pageSize - 1:
        raw_input()

    return lPageContent


def getChecksum(blocks):

    # Try older method - Add and Pack into integer.
    lChecksum = bytearray(1)
    for x in blocks:
        lChecksum[0] = (lChecksum[0] + x) % 256

    return lChecksum[0]


# port and file are REQUIRED at minimum, otherwise a ValueError is raised
def getCommandlineArgs():
    # we have more arguments
    port = ''
    file = ''
    try:
        opts, args = getopt.getopt(sys.argv[1:],
                                   "hp:f:",
                                   ["port=", "file="])
        for opt, arg in opts:
            print 'checking...'
            if opt == '-h':
                print 'usage: ' + sys.argv[0] + ' -p port -f hexfile'
            elif opt in ("-p", "--port"):
                port = arg
                print 'got port: ' + port
            elif opt in ("-f", "--file"):
                file = arg
                print 'got file: ' + file

        print port
        print file
        if len(port) is 0 or len(file) is 0:
            print 'not enough arguments supplied.'
            # print 'usage: ' + sys.argv[0] + ' -p port -f hexfile'
            raise ValueError('GetoptError detected')
            # sys.exit(2)
        else:
            return (port, file)
            # sHexFilePath = file
            # sDeviceFile = port
    except getopt.GetoptError:
        print 'getopt error'
        # print 'usage: ' + sys.argv[0] + ' -p port -f hexfile'
        raise ValueError('GetoptError detected')
        return file, port
        # sys.exit(2)
# Class


# Main Program ###
def main():
    printIntroMessage()
    if sys.argv > 1:
        try:
            p, f = getCommandlineArgs()
            sDeviceFile = p
            sHexFilePath = f
        except ValueError:
            print 'usage: ' + sys.argv[0] + ' -p port -f hexfile'
    else:
        # use default settings
        print 'no command line switches detected: using default settings'

    print str('-' * (len(sHexFilePath) + 20))
    print "Hex File Path = \"" + sHexFilePath + "\""
    print str('-' * (len(sHexFilePath) + 20))

    # Fetching Hex File and Storing
    hexFile = IntelHex(sHexFilePath)

    if sGenerateBinary == "y":
        # Create a Binary File of this Hex File
        sBinFilePath = string.replace(sHexFilePath, ".hex", ".bin")
        logging.debug("Binary File Path : %s", sBinFilePath)
        hexFile.tofile(sBinFilePath, format='bin')

    # Obtain the actual Binary content from the Hex File
    binArray = hexFile.tobinarray()

    sPort = serial.Serial(port=sDeviceFile,
                          baudrate=sInitialDeviceBaud,
                          parity=serial.PARITY_NONE,
                          stopbits=serial.STOPBITS_ONE,
                          bytesize=serial.EIGHTBITS)

    sPort.reset_input_buffer()
    sPort.reset_output_buffer()
    sPort.flush()

    # Setting Initial State of RTS Bit to False
    sPort.rts = False

    # Reseting the board by toggling DTR
    sPort.dtr = False

    # Reading a Byte from SJOne
    msg = sPort.read(1)

    if msg is ByteReference[0]:

        sPort.write(ByteReference[1])

        logging.debug("Initial Handshake Initiated! - Received ")

        msg = sPort.read(1)

        if msg is ByteReference[2]:
            logging.debug("Received " + (str)(repr(msg)) + ", Sending Control Word..")

            lControlWordInteger = getControlWord(sDeviceBaud, sCPUSpeed)
            lControlWordPacked = struct.pack('<i', lControlWordInteger)

            msg = sPort.write(bytearray(lControlWordPacked))

            if msg != 4:
                logging.error("Error - Sending control word failed")
            else:
                logging.debug("Sending Control Word Successful!")

                msg = sPort.read(1)

                if msg != lControlWordPacked[0]:
                    logging.error("Error - Failed to receive Control Word Ack")
                else:
                    logging.debug("Ack from SJOne received!")

                    if sDeviceBaud != sInitialDeviceBaud:
                        # Switch to new BaudRate here.
                        logging.debug("Requested Baudrate different from Default. Changing Baudrate..")

                        sPort.baudrate = sDeviceBaud

                    else:
                        logging.debug("BaudRate same as Default")

                    # Read the CPU Desc String
                    msg = sPort.read(1)

                    if msg != SpecialChar['Dollar']:
                        logging.error("Failed to read CPU Description String")
                    else:
                        logging.debug("Reading CPU Desc String..")

                        CPUDescString = SpecialChar['Dollar']
                        while True:
                            msg = sPort.read(1)

                            if msg == SpecialChar['NextLine']:
                                break

                            CPUDescString = CPUDescString + msg

                        logging.debug("CPU Description String = %s", CPUDescString)

                        boardParameters = getBoardParameters(CPUDescString)

                        # Receive OK from SJOne
                        msg = sPort.read(1)

                        if msg != SpecialChar['OK']:
                            logging.error("Error - Failed to Receive OK")
                        else:
                            logging.debug("OK Received! Sending Block")

                        # Send Dummy Blocks -
                        # Update : We can send the actual blocks itself.


                        # Sending Blocks of Binary File
                        totalBlocks = (len(binArray) * 1.0 / int(boardParameters['BlockSize']))
                        logging.debug("Total Blocks = %f", totalBlocks)

                        paddingCount = len(binArray) - ((len(binArray)) % int(boardParameters['BlockSize']))
                        logging.debug("Total Padding Count = %d", paddingCount)

                        totalBlocks = math.ceil(totalBlocks)
                        print "Total # of Blocks to be Flashed = ", totalBlocks

                        # Pad 0's to binArray if required.
                        binArray = bytearray(binArray)
                        binArray += (b'\x00' * paddingCount)

                        blockCount = 0
                        sendDummy = False
                        # sendDummy = True
                        blockContent = bytearray(int(boardParameters['BlockSize']))

                        if sendDummy is True:
                            logging.debug("FLASHING EMPTY BLOCKS")

                        while blockCount < totalBlocks:
                            print "--------------------"
                            blockCountPacked = struct.pack('<H', blockCount)

                            msg = sPort.write(blockCountPacked[1])
                            if msg != 1:
                                logging.error("Error in Sending BlockCountLowAddr")

                            msg = sPort.write(blockCountPacked[0])
                            if msg != 1:
                                logging.error("Error in Sending BlockCountHiAddr")

                            logging.debug("BlockCounts = %d", blockCount)

                            if sendDummy is False:
                                blockContent = getPageContent(binArray, blockCount, int(boardParameters['BlockSize']))

                            msg = sPort.write(blockContent)
                            if msg != len(blockContent):
                                logging.error("Error - Failed to sending Data Block Content")
                                break

                            # printContent(blockContent)

                            checksum = bytearray(1)

                            checksum[0] = getChecksum(blockContent)

                            logging.debug("Checksum = %d[0x%x]", checksum[0], checksum[0])

                            msg = sPort.write(checksum)
                            logging.debug("Size of Block Written = %d", msg)

                            if msg != 1:
                                logging.error("Error - Failed to send Entire Data Block")

                            msg = sPort.read(1)
                            if msg != SpecialChar['OK']:
                            	logging.error("Failed to Receive Ack.. Retrying #" + str(blockCount))
                            else:
                                print "Block # " + str(blockCount) + " flashed!"
                                blockCount = blockCount + 1

                            print "--------------------"

                    if blockCount != totalBlocks:
                        logging.error("Error - All Blocks not Flashed")
                        logging.error("Total = " + str(totalBlocks))
                        logging.error("# of Blocks Flashed = " + str(blockCount))
                    else:
                        print "Flashing Successful!"
                        endTxPacked = bytearray(2)
                        endTxPacked[0] = 0xFF
                        endTxPacked[1] = 0xFF

                        msg = sPort.write(bytearray(endTxPacked))

                        if msg != 2:
                            logging.error("Error in Sending End Of Transaction Signal")

                        msg = sPort.read(1)
                        logging.debug("Received Ack = " + str(msg))

                        if msg != SpecialChar['STAR']:
                            logging.error("Error - Final Ack Not Received")

    else:
        logging.error("Timed Out!")

    sPort.baudrate = sInitialDeviceBaud

    sPort.close()


if __name__ == "__main__":
    main()
