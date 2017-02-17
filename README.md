# pyFlash-Hyperload
Version : 2.1

## About the Tool:
A firmware flashing tool for SJOne using Python. This is based on the 'Hyperload' Protocol for flashing images at high speeds.

The original source is here: https://gitlab.com/akshay-vijaykumar/pyFlash-Hyperload

## Required Packages

* python2   [v]
* pyserial `[v3.0.1]`
    - `pip install pyserial`
* intelhex `[v2.0]`
    - `pip install intelhex`

## Steps to Run:
### Method 1 - GUI version
Run the script with the `-g` flag to enable the GUI mode

```
./pyFlashHyperload.py -g
```

### Method 2 - Commandline arguments
This method can be useful for incorporating into a Makefile or Eclipse rule to automatically program the board. 

* Usage: 
    - short-hand: `python pyFlashHyperload.py -p port -f file [-b baud]`
    - long-hand: `python pyFlashHyperload.py --port=port --file=file [--baud=baud]`


**Note:** the optional switch, `-b baud`, represents the baud rate that will be used to **flash the board** It's recommended to choose a higher value. The default is set to `1000000 baud`. Initial communication with the board will always be done at 38.4K baud.

Example:
```
./pyFlashHyperload.py -p /dev/tty.usbserial-A503JOHW -f /path/to/your/file.hex
```

#### Tip
If you're running a commandline build with Makefiles, it's recommended to symlink the main script to your working directory and create a rule in the make file.  

symlink python script to working directory
> this step is optional and is more for convenience. allows you to write your Makefile rules using relative paths instead of absolute paths.

```bash
cd $(WORKING_DIRECTORY)
ln -s /path/to/hyperload/pyFlashHyperload.py pyFlashHyperload.py
```

Add a rule to your Makefile:

```make
flash:
    ./pyFlashHyperload.py -p /dev/tty.usbserial-A503JOHW -f $(WORKING_DIRECTORY)/build/program.hex
```

Program your board with `make flash`


### Method 3 - Editing the source (not recommended)
    - Modify pyFlashHyperload.py with the required Filepaths and Baudrate.
    - Run "sudo python pyFlashHyperload.py"

## Development

### Notes
* Make sure to not mix `spaces` with `tab` tabbing on the editor. Stick with 4 spaces for consistency.
* [Hyperload Protocol](http://www.socialledge.com/sjsu/index.php?title=Hyperload_Protocol)

### TODO

- [x] Display platform information
- [x] Enable debug/release switch
- [ ] Create ~/.pyFlash and store last used options for flashing
- [ ] Handle exceptions
- [ ] Ensure packing is done based on Endianness
- [x] Rewrite program with classes using this as the backbone
- [x] Incorporate design decisions keeping GUI in mind
- [ ] Add code comments
- [ ] Restructure flashing methods to be "phase 1/2/3" as defined in Hyperload protocol
- [ ] Thread GUI to keep app responsive during flash

### Issues Faced
1. Handling Bytes were hard - Use bytearray for most of the IO related functions. Difference between bytes and bytearray is that the latter is mutable. 
2. Bytes are types that are not mutable. Any changes done on them will cause a new alloc + concat and reassigning.

## CHANGELOG
### v2.1 - 2017-02-16
* Fixed repeated flash with GUI mode (close serial port after flashing)
* Removed leftover buttons on GUI from testing
* Fixed `-b baud` command line flag switch

### v2.0 - 2017-02-15
> Only has been tested on macOS Sierra

* Added GUI interface (thanks @mrgrantham)

### v1.1 - 2017-02-11
> Only has been tested on macOS Sierra

* Added command line settings change support
* Converted all tabs to spaces and remove line endings
* Moved main code into a main function 
* Split off many portions of the main function into smaller functions in preparation for TODO list
* Organized main function into Phase 1, Phase 2, and Phase 3
* Forked repo from https://gitlab.com/akshay-vijaykumar/pyFlash-Hyperload

### v1.0 - 2016-02-15
* Working Skeleton for Flashing a Hex file to SJOne comeplete!
* Initial release
