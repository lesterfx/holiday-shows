# Holiday Pixels

Holiday pixels is built to handle a pixel strip and relays for use in a holiday light show. It includes a number of realtime animations, with underlying physics system. It also includes images, with all corresponding projects, for several animations, including my Christmas light show (see https://youtu.be/TRXpL8alP7s).

Higher level, it also handles scheduling of different animations throughout the year, and time of day for running the display.

## dependencies

all of the following need to be done as root because the code must run as root

    sudo pip3 install rpi_ws281x adafruit-circuitpython-neopixel
    sudo python3 -m pip install --force-reinstall adafruit-blinka
    sudo python3 -m pip install --upgrade pip
    sudo python3 -m pip install --upgrade Pillow

if PIL continues giving errors, the following worked for me:

    sudo apt-get install libopenjp2-7
    sudo apt-get install libtiff5
