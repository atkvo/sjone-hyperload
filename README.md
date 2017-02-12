# pyFlash-Hyperload
Version : 1.1

## About the Tool:
A firmware flashing tool for SJOne using Python. This is based on the 'Hyperload' Protocol for flashing images at high speeds.

## Required Packages

* python2   [v]
* pyserial `[v3.0.1]`
    - `pip install pyserial`
* intelhex `[v2.0]`
    - `pip install intelhex`

## Steps to Run:
### Method 1 - Editing the source
	- Modify pyFlash-Hyperload.py with the required Filepaths and Baudrate.
	- Run "sudo python pyFlash-Hyperload.py"

### Method 2 - Commandline arguments
This method can be useful for incorporating into a Makefile or Eclipse rule to automatically program the board

Usage: 
`python pyFlash-Hyperload.py -p port -f file [-b baud]`
or 
`python pyFlash-Hyperload.py --port=port --file=file [--baud=baud]`


Example:
```
./pyFlash-Hyperload.py -p /dev/tty.usbserial-A503JOHW -f /Users/[username]/Workspace/eclipse/temp/Debug/test.hex
```


## Development

### Notes

* Make sure to not mix `spaces` with `tab` tabbing on your editor. 

### Things to Do:

```
1. Display Platform Information                               [DONE]
2. Enable a Debug/Release Switch                              [DONE]
3. Create ~/.pyFlash and store last used options for Flashing [PEND]
4. Handle Exceptions                                          [PEND]
5. Ensure packing is done based on Endianness                 [PEND]
6. Re-write program with classes using this as the backbone.  [PEND]
7. Incorporate design decisions keeping the GUI in mind       [PEND]
```

### Issues Faced
1. Handling Bytes were hard - Use bytearray for most of the IO related functions. Difference between bytes and bytearray is that the latter is mutable. 
2. Bytes are types that are not mutable. Any changes done on them will cause a new alloc + concat and reassigning.

## CHANGELOG
### v1.1 - 2017-02-11
> Only has been tested on macOS Sierra

* Added command line settings change support
* Converted all tabs to spaces and remove line endings
* Moved main code into a main function 
* Forked repo from https://gitlab.com/akshay-vijaykumar/pyFlash-Hyperload

### v1.0 - 2016-02-15
* Working Skeleton for Flashing a Hex file to SJOne comeplete!
* Initial release