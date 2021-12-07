# Holiday Pixels

Holiday pixels is built to handle a pixel strip and relays for use in a holiday light show. It also includes images, with all corresponding projects, for several animations, including my Christmas light show (see https://youtube.com/playlist?list=PL5_7cNnkl5ej_f4FlKBPtnKV2Qg7zWjKU).

Higher level, it also handles scheduling of different animations throughout the year, and time of day for running the display.

## dependencies

all of the following need to be done as root because the code must run as root to control pixel strips

    sudo pip3 install rpi_ws281x adafruit-circuitpython-neopixel
    sudo python3 -m pip install --force-reinstall adafruit-blinka
    sudo python3 -m pip install --upgrade pip
    sudo python3 -m pip install --upgrade Pillow

if PIL continues giving errors, the following worked for me:

    sudo apt-get install libopenjp2-7
    sudo apt-get install libtiff5

## hardware

The main code is built to run on a raspberry pi, with the primary handling scheduling, dispatch, and audio. additional devices can be used:

- additional raspberry pi's for additional pixel strips, beyond the one that may be attached to the primary pi
- arduinos to switch relays
- [future] arduinos to control short pixel strips or predefined animations
- [future] arduino to display a countdown
