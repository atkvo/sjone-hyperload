#!/usr/bin/env python
"""
# SJSU - AV #

# CHANGELOG:
# 2017-02-11 : Added command line settings change support
# 2016-02-15 : Working Skeleton for Flashing a Hex file to SJOne comeplete!
"""

import serial
import string
import struct
import math
import serial.serialutil
import logging
import sys
import getopt
import pyFlashHyperloadGUI
from intelhex import IntelHex



# LOGGING OPTIONS #######
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



class HLBackend:

    def __init__(self):

        ###############################################################################
        # CONFIGURATION FOR pyFlash - Hyperload #######################################
        ###############################################################################
        self.sDeviceFile = "/dev/tty.usbserial-A503JOND"   # Device File Path
        self.sDeviceBaud = 38400          # Suitable Device Baud Rate
        self.sHexFilePath = "/Users/dev/Programming_Projects/sjone-hyperload/lpc1758_freertos_GPIO.hex"
        self.sGenerateBinary = "y"  # "y" - Yes | "n" - No
        ###############################################################################

        self.ApplicationVersion = "1.1"
        self.ToolName = "pyFLASH - HYPERLOAD"
        self.ToolInfo = "Flashing Tool for SJOne"
        self.BaudList = [4800, 9600, 19200, 38400]
        self.ControlWordList = b'\x80\xf8\xfe\xff'
        self.SpecialChar = {'Dollar': '$', 'OK': '!', 'NextLine': '\n', 'STAR': '*'}
        self.sCPUSpeed = 48000000
        self.sInitialDeviceBaud = 38400

        self.ByteReference = b'\xff\x55\xaa'

    # Common Util Functions
    def printIntroMessage(self):
        print "#######################"
        print " ", self.ToolName
        print self.ToolInfo
        print "#######################"
        print "Version    : ", self.ApplicationVersion
        print "Build Type : ", PYFLASH_BUILD_LEVEL
        print "#######################"

        return


    def printBytes(self,mymsg):

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


    def getBoardParameters(self,descString):
        boardParameters = {'Board': '',
                           'BlockSize': '',
                           'BootloaderSize': '',
                           'FlashSize': ''}

        # Parsing String to obtain required Board Parameters
        boardParametersList = descString.split(':')

        boardParameters['Board'] = boardParametersList[0]
        boardParameters['BlockSize'] = boardParametersList[1]
        boardParameters['BootloaderSize'] = (int(boardParametersList[2]) * 2)
        boardParameters['FlashSize'] = boardParametersList[3]

        print "\n***** Board Information ********"
        print "Board           = {}".format(boardParameters['Board'])
        print "Block Size      = {} B".format(boardParameters['BlockSize'])
        print "Bootloader Size = {} B".format(boardParameters['BootloaderSize'])
        print "Flash Size      = {} KB".format(boardParameters['FlashSize'])
        print "*********************************\n"

        return boardParameters


    def printContent(self,lContent):

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


    def getControlWord(self,baudRate, cpuSpeed):
        # TODO : Currently using known values. Replace with actual formula
        logging.debug("Retrieving Control Word")

        controlWord = ((cpuSpeed / (baudRate * 16)) - 1)

        return controlWord


    def getPageContent(self, bArray, blkCount, pageSize):

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


    def getBinaryFromIHex(self,filepath, generateBin):
        # Fetching Hex File and Storing
        hexFile = IntelHex(filepath)

        if generateBin == "y":
            # Create a Binary File of this Hex File
            binFilePath = string.replace(filepath, ".hex", ".bin")
            logging.debug("Binary File Path : %s", binFilePath)
            hexFile.tofile(binFilePath, format='bin')

        # Obtain the actual Binary content from the Hex File
        binary = hexFile.tobinarray()
        return binary


    def padBinaryArray(self,binArray, blockSize):
        paddingCount = (len(binArray) - (len(binArray)
                        % blockSize))
        logging.debug("Total Padding Count = %d", paddingCount)
        # Pad 0's to binArray if required.
        binArray = bytearray(binArray)
        binArray += (b'\x00' * paddingCount)
        return binArray


    def getChecksum(self,blocks):

        # Try older method - Add and Pack into integer.
        lChecksum = bytearray(1)
        for x in blocks:
            lChecksum[0] = (lChecksum[0] + x) % 256

        return lChecksum[0]


    # port and file are REQUIRED at minimum, otherwise a ValueError is raised
    def getCommandlineArgs(self):
        # we have more arguments
        port = ''
        file = ''
        baud = -1
        gui = 0
        try:
            opts, args = getopt.getopt(sys.argv[1:],
                                       "ghp:f:b:",
                                       ["port=", "file=", "baud="])
            for opt, arg in opts:
                if opt == '-h':
                    print 'usage: ' + sys.argv[0] + ' -p port -f hexfile'
                elif opt in ("-g","--gui"):
                    gui = 1
                elif opt in ("-p", "--port"):
                    port = arg
                    print 'got port: ' + port
                elif opt in ("-f", "--file"):
                    file = arg
                    print 'got file: ' + file
                elif opt in ("-b", "--baud"):
                    try:
                        baud = int(arg)
                    except ValueError:
                        raise ValueError('Baud rate invalid: ' + arg + 'Exiting.')
            print port
            print file
            if not gui:
                if len(port) is 0 or len(file) is 0:
                    print 'not enough arguments supplied.'
                    # print 'usage: ' + sys.argv[0] + ' -p port -f hexfile'
                    raise ValueError('GetoptError detected')
                    # sys.exit(2)
                else:
                    return (port, file, baud, gui)
                    # self.sHexFilePath = file
                    # self.sDeviceFile = port
            else:
                return (port, file, baud, gui)
        except getopt.GetoptError:
            print 'getopt error'
            # print 'usage: ' + sys.argv[0] + ' -p port -f hexfile'
            raise ValueError('GetoptError detected')
            return file, port
            # sys.exit(2)
    # Class


    # params binArray, blockContent, blockSize, blockCount, totalBlocks
    def flash(self,sPort, binArray, blockContent,
              blockSize, totalBlocks, sendDummy=False):
        blockCount = 0
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
                blockContent = self.getPageContent(binArray, blockCount, blockSize)

            msg = sPort.write(blockContent)
            if msg != len(blockContent):
                logging.error("Error - Failed to sending Data Block Content")
                break

            # printContent(blockContent)

            checksum = bytearray(1)

            checksum[0] = self.getChecksum(blockContent)

            logging.debug("Checksum = %d[0x%x]", checksum[0], checksum[0])

            msg = sPort.write(checksum)
            logging.debug("Size of Block Written = %d", msg)

            if msg != 1:
                logging.error("Error - Failed to send Entire Data Block")

            msg = sPort.read(1)
            if msg != self.SpecialChar['OK']:
                logging.error(
                    "Failed to Receive Ack.. Retrying #{}".format(blockCount))
            else:
                print "Block # " + str(blockCount) + " flashed!"
                blockCount = blockCount + 1

            print "--------------------"
        return blockCount


    def prematureExit(self,serialport, message):
        logging.error("{}. Exiting...".format(message))
        serialport.baudrate = self.sInitialDeviceBaud
        serialport.close()
        sys.exit(2)


    def getHandshakeStatus(self,sp, handshakeBytes):
        """
        handshakeBytes expects the handshake
         protocol bytes in alternating order

        read, write, read, write, read (must end on a read)
        """
        # reset SJOne board
        sp.rts = False
        sp.dtr = False

        # read from SJOne for bootloader signal
        msg = sp.read(1)

        if msg is handshakeBytes[0]:
            # SJOne bootloader is active, begin handshake
            # skip the first handshake since it's done now
            for i in xrange(1, len(handshakeBytes) - 1):

                # send and read next handshake protocol
                sp.write(handshakeBytes[i])
                msg = sp.read(1)

                if msg is handshakeBytes[i + 1]:
                    print 'Handshake {} received'.format(i)
                else:
                    print 'Handshake {} timed out'.format(i)
                    return False
            return True
        else:
            return False


    def setBoardBaud(self,sp, baud, cpuSpeed):
        lControlWordInteger = self.getControlWord(baud, cpuSpeed)
        lControlWordPacked = struct.pack('<i', lControlWordInteger)

        bytesWritten = sp.write(lControlWordPacked)

        if bytesWritten == len(lControlWordPacked):
            msg = sp.read(1)
            if msg != lControlWordPacked[0]:
                print "Error: Failed to receive control word ACK"
                return False
            else:
                print "Success: board set to {} baud.".format(baud)
                return True
        else:
            print 'Error: control word not sent successfully'
            return False


    def getCpuDescription(self,sp):
        """ Phase 2.1 Should be called immediately after setting the board baud rate.
            Example CPU description: "$LPC1758:4096:2048:512\n"
        """
        print 'Getting CPU description'
        msg = sp.read(1)

        if msg is self.SpecialChar['Dollar']:
            # begin building CPU description string
            CPUDescString = self.SpecialChar['Dollar']
            while True:
                msg = sp.read(1)
                if msg == self.SpecialChar['NextLine']:
                    return CPUDescString
                else:
                    CPUDescString = CPUDescString + msg
        else:
            return ""


    def hyperloadPhase1(self,sp, baud):
        """
        Args:
            sp   (Serial) : serial port to communicate with the SJOne board
            baud (int)    : desired baud rate to program the board at
        Returns:
            (success, errMsg): is a tuple
        Raises:

        """

        # Protocol Phase 1
        if self.getHandshakeStatus(sp, self.ByteReference) is False:
            return (False, "Phase 1 Error: Handshake failure.")

        if self.setBoardBaud(sp, baud, self.sCPUSpeed) is False:
            return (False, "Phase 1 Error: Setting board baud rate failure.")

        if baud != self.sInitialDeviceBaud:
            # Switch to new BaudRate here.
            logging.debug("Requested Baudrate different from Default. \
                           Changing Baudrate..")
            sp.baudrate = baud
        else:
            logging.debug("BaudRate same as Default")

        return (True, "Phase 1 complete")


    def hyperloadPhase2(self,sp):
        # Protocol Phase 2
        descr = self.getCpuDescription(sp)
        if len(descr) > 0:
            msg = sp.read(1)  # check for OK response from SJOne
            if msg != self.SpecialChar['OK']:
                logging.error("Phase 2 Error: Failed to receive OK")
                return (False, "", "Phase 2 Error: Failed to receive OK")
            else:
                logging.debug("Phase 2 complete")
                return (True, descr, "Phase 2 complete")
        else:
            return (False, descr, "Phase 2 Error: Failed to get CPU description")

    def configureSerial(self):
        self.sPort = serial.Serial(port=self.sDeviceFile,
                              baudrate=self.sInitialDeviceBaud,
                              parity=serial.PARITY_NONE,
                              stopbits=serial.STOPBITS_ONE,
                              bytesize=serial.EIGHTBITS)

        self.sPort.reset_input_buffer()
        self.sPort.reset_output_buffer()
        self.sPort.flush()

    def CLmode(self):

        print str('-' * (len(self.sHexFilePath) + 20))
        print "Hex File Path = \"" + self.sHexFilePath + "\""
        print str('-' * (len(self.sHexFilePath) + 20))

        configureSerial()

        # ---- Hyperload Phase 1 ----
        status, errMsg = self.hyperloadPhase1(self.sPort, self.sDeviceBaud)

        if status is False:
            # failure. don't flash
            self.prematureExit(self.sPort, errMsg)
        else:
            pass
        # ---- Phase 1 complete ----

        # ---- Hyperload Phase 2 ----
        status, CPUDescString, errMsg = self.hyperloadPhase2(self.sPort)

        if status is False:
            # phase 2 failure. abort.
            self.prematureExit(self.sPort, errMsg)
        else:
            pass
        # ---- Phase 2 complete ----

        logging.debug("CPU Description String = %s", CPUDescString)

        # Prepare for phase 3
        boardParameters = self.getBoardParameters(CPUDescString)

        binArray = self.getBinaryFromIHex(self.sHexFilePath, self.sGenerateBinary)
        blockSize = int(boardParameters['BlockSize'])
        totalBlocks = (len(binArray) * 1.0) / blockSize
        totalBlocks = math.ceil(totalBlocks)
        binArray = self.padBinaryArray(binArray, blockSize)
        blockContent = bytearray(blockSize)

        logging.debug("Total Blocks = %f", totalBlocks)
        print "Total # of Blocks to be Flashed = ", totalBlocks

        # Send Dummy Blocks -
        # Update : We can send the actual blocks itself.
        sendDummy = False
        if sendDummy is True:
            logging.debug("FLASHING EMPTY BLOCKS")

        # ---- Hyperload Phase 3 ----
        # Sending Blocks of Binary File
        blockCount = self.flash(sPort,
                           binArray,
                           blockContent,
                           blockSize,
                           totalBlocks,
                           sendDummy)
        if blockCount != totalBlocks:
            logging.error("Error - All Blocks not Flashed")
            logging.error("Total = {}".format(totalBlocks))
            logging.error("# of Blocks Flashed = {}"
                          .format(blockCount))
        else:
            print "Flashing Successful!"
            endTxPacked = bytearray(2)
            endTxPacked[0] = 0xFF
            endTxPacked[1] = 0xFF

            msg = sPort.write(bytearray(endTxPacked))

            if msg != 2:
                logging.error("Error Sending \
                    End Of Transaction Signal")

            msg = sPort.read(1)
            logging.debug("Received Ack = " + str(msg))

            if msg != self.SpecialChar['STAR']:
                logging.error("Error - Final Ack Not Received")
        # ---- Phase 3 Complete ----

        sPort.baudrate = self.sInitialDeviceBaud
        sPort.close()

def main():

    gui = 0

    HL = HLBackend();

    HL.printIntroMessage()
    if len(sys.argv) > 1:
        try:
            p, f, b, gui = HL.getCommandlineArgs()
            HL.sDeviceFile = p
            HL.sHexFilePath = f
            if b > 0:
                HL.sDeviceBaud = b  # set to user specified baud
            else:
                pass  # fall back to hard-coded baud rate

        except ValueError:
            print 'usage: ' + sys.argv[0] + ' -p port -f hexfile [-b baudrate]'
            sys.exit(2)
    else:
        # use default settings
        print 'no command line switches detected: using default settings'
        pass

    if gui:
        pyFlashHyperloadGUI.MainWindow(HL).mainloop();
    else:
        HL.CLmode()

if __name__ == "__main__":
    main()
