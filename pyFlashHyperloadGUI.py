# Test GUI

from Tkinter import *
import pyFlashHyperload
import ttk
import tkFileDialog
from subprocess import Popen, PIPE


class MainWindow(Frame):

    def __init__(self, HLBackend):

        Frame.__init__(self)

        self.BackEnd = HLBackend
        self.master.title("pyFlash Hyperload")
        self.master.config(height=800, width=300)
        # self.master.minsize(400, 200)
        self.grid(sticky=N + S + E + W, padx=(15, 15), pady=(15, 15))
        # Code to add widgets will go here...
        Label(self, text="FLASH Programming File (*.HEX)").grid(row=0, sticky=W + N + S, columnspan=2, padx=(10, 10))
        self.hex_filepath = StringVar()
        self.tbox_hex_filepath = Entry(self, textvariable=self.hex_filepath)
        self.tbox_hex_filepath.grid(row=1, column=0, sticky=E + W + N + S, padx=(10, 10), pady=(10, 10), columnspan=3)

        Button(self, text='Open', command=self.b_open).grid(row=1, column=3, padx=(10, 10), pady=(10, 10), sticky=E + W + N + S)
        Button(self, text='Clear', command=self.b_clear).grid(row=1, column=4, padx=(10, 10), pady=(10, 10), sticky=E + W + N + S)
        Button(self, text='Flash', command=self.b_flash).grid(row=2, column=3, columnspan=2, padx=(10, 10), pady=(10, 10), sticky=E + W + N + S)

        pbar_style = ttk.Style()
        pbar_style.theme_use('default')
        pbar_style.configure("gray.Horizontal.TProgressbar", foreground='blue', background='white')

        self.progvar = IntVar(self)
        self.progbar = ttk.Progressbar(self, orient=HORIZONTAL, length=500, style="gray.Horizontal.TProgressbar", variable=self.progvar, mode='determinate')
        self.progbar.grid(sticky=E + W + N + S, row=2, column=0, columnspan=3, padx=(13, 10), pady=(10, 10))

        Label(self, text="Select Serial Device").grid(row=3, sticky=W + N + S, padx=(10, 10), pady=(10, 5))

        # Captures STDOUT from ls command for option menu
        stdout = Popen('ls -1 /dev/tty.*', shell=True, stdout=PIPE).stdout
        output = stdout.read()

        self.devices = list()
        self.devices.extend(output.split())
        self.selected_device = StringVar(self)  # stores the selection from drop down menu
        self.deviceOptions = OptionMenu(self, self.selected_device, "", *self.devices)
        self.deviceOptions.grid(sticky=E + W + N + S, row=4, columnspan=3, padx=(8, 10))
        # set a default usbserial device

        self.validDevice = self.findSubString(self.devices, "usbserial")

        if self.validDevice:
            self.selected_device.set(self.devices[self.validDevice])

        self.selected_baudRate = StringVar(self)  # stores baud rate selection
        Label(self, text="Flash Baud Rate").grid(row=5, sticky=W + N + S, padx=(10, 10), pady=(10, 5))
        self.baudRate = OptionMenu(self, self.selected_baudRate, "", *self.BackEnd.BaudList)
        self.baudRate.grid(sticky=E + W + N + S, row=6, columnspan=3, padx=(8, 10))

        # set default to the fastest speed
        maxFlashSpeedIndex = len(self.BackEnd.BaudList) - 1
        self.selected_baudRate.set(self.BackEnd.BaudList[maxFlashSpeedIndex])

        # Device Labels
        Label(self, text="Device Information", justify=CENTER, width=15).grid(row=4, sticky=E + W + N + S, column=3, columnspan=2, padx=(10, 10))
        Label(self, text="Board:", justify=RIGHT, anchor=E).grid(row=5, sticky=E + W + N + S, column=3, columnspan=1, padx=(10, 10))
        Label(self, text="Block Size:", justify=RIGHT, anchor=E).grid(row=6, sticky=E + W + N + S, column=3, columnspan=1, padx=(10, 10))
        Label(self, text="Bootloader Size:", justify=RIGHT, anchor=E).grid(row=7, sticky=E + W + N + S, column=3, columnspan=1, padx=(10, 10))
        Label(self, text="Flash Size:", justify=RIGHT, anchor=E).grid(row=8, sticky=E + W + N + S, column=3, columnspan=1, padx=(10, 10))

        # Device Information pulled from
        self.l_board = Label(self, text="<-->", justify=LEFT, anchor=W)
        self.l_board.grid(row=5, column=4, sticky=W + N + S, columnspan=1, padx=(10, 10))
        self.l_block = Label(self, text="<-->", justify=LEFT, anchor=W)
        self.l_block.grid(row=6, column=4, sticky=W + N + S, columnspan=1, padx=(10, 10))
        self.l_bootloader = Label(self, text="<-->", justify=LEFT, anchor=W)
        self.l_bootloader.grid(row=7, column=4, sticky=W + N + S, columnspan=1, padx=(10, 10))
        self.l_flash = Label(self, text="<-->", justify=LEFT, anchor=W)
        self.l_flash.grid(row=8, column=4, sticky=W + N + S, columnspan=1, padx=(10, 10))

    def commit_parameters(self):
        if(self.selected_device.get() != ""):
            self.BackEnd.setPort(self.selected_device.get())
        else:
            return False
        if(self.selected_baudRate.get() != ""):
            self.BackEnd.setFlashBaudRate(self.selected_baudRate.get())
        else:
            return False
        if(self.hex_filepath.get() != ""):
            self.BackEnd.setFilePath(self.hex_filepath.get())
        else:
            return False
        return True


    def set_deviceInfo(self):
        self.l_board.config(text=self.BackEnd.boardParameters['Board'])
        self.l_block.config(text=self.BackEnd.boardParameters['BlockSize'])
        self.l_bootloader.config(text=self.BackEnd.boardParameters['BootloaderSize'])
        self.l_flash.config(text=self.BackEnd.boardParameters['FlashSize'])

    def b_open(self):
        self.hex_filepath.set(tkFileDialog.askopenfilename())
        self.commit_parameters()
        self.BackEnd.configureSerial()
        self.BackEnd.preFlashPhases()
        self.set_deviceInfo()

    def b_clear(self):
        self.hex_filepath.set("")

    def b_flash(self):
        if (self.commit_parameters()):
            self.BackEnd.configureSerial()
            self.BackEnd.preFlashPhases()
            self.set_deviceInfo()
            self.BackEnd.flashPhase(self.updateProgress)
            self.BackEnd.closeSerial()
        else:
            print "Unable to Commit: Not Enough Parameters Selected"

    def updateProgress(self, progressValue):
        self.progvar.set(progressValue)
        self.update()

    def findSubString(self, sourceList, substring):
        print "substring: " + substring
        print "Source string: " + str(sourceList)

        for index, string in enumerate(sourceList):
            print "string: " + string

            if substring in string:
                print index
                return index
        return -1


if __name__ == "__main__":
    MainWindow().mainloop()
