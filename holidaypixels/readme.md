# Holiday Pixels

Holiday pixels is built to handle pixel strips and relays for use in a holiday light show. It also includes images, with all corresponding projects, for several animations, including my Christmas light show (see https://youtube.com/playlist?list=PL5_7cNnkl5ej_f4FlKBPtnKV2Qg7zWjKU).

Higher level, it also handles scheduling of different animations throughout the year, and time of day for running the display.

# installation

Clone the repo into your environment, and running the following to install dependencies.

Note that `sudo` should be used to allow the packages to be run by root.

    sudo pip3 install rpi_ws281x adafruit-circuitpython-neopixel pygame
    sudo python3 -m pip install --force-reinstall adafruit-blinka
    sudo python3 -m pip install --upgrade pip
    sudo python3 -m pip install --upgrade Pillow
    sudo apt install libsdl2-2.0-0
    sudo apt-get install git curl libsdl2-mixer-2.0-0 libsdl2-image-2.0-0 libsdl2-2.0-0

if PIL continues giving errors, the following worked for me:

    sudo apt-get install libopenjp2-7
    sudo apt-get install libtiff5

# hardware

The main code is built to run on one or more Raspberry Pi computers, with the primary handling scheduling, dispatch, and audio. Additional devices can be used:

- Additional Raspberry Pi computers to control additional pixel strips, beyond the one that may be attached to the primary. Should run with `--remote` flag.
- Arduinos to switch relays, running the `UDPRelayControl` sketch.
- [future] Arduino to control short pixel strips or predefined animations
- [future] Arduino to display a countdown

# config.json

All adjustments should be possible in here. If not, pull requests are most welcome.

## globals

Globals stores the configuration of relays, pixel strips, and the remotes that control them.

`"audio_delay"` specifies how long (in seconds) to wait after telling the audio to play before starting animation.

`"strips"` defines the individual pixel strips. Each named strip has the following arguments:

- `"ip"`: The IP address to communicate over. If the IP provided is the same as the controller, it will automatically be replaced with `null` and run locally.
- `"port"`: Which port to connect to (when not local).
- `"pin"`: Which GPIO pin the pixels are connected to. Only some are allowed, so make sure you have a good reason not to just stick to the default of `18`.
- `"pixel_order"`: Some strips expect the data in a different order than the default of `"RGB"`. In that case, specify the alternate order here (case-insensitive).
- `"frequency"`: The expected frequency of the pixel strip. Refer to the strip's data sheet for this information.
- `"dma"`: I believe there are two DMA channels on the Raspberry Pi. Channel 10 is the only one that has been tested.
- `"invert"`: Reverse the HIGH and LOW of the PWM signal sent to the strip.
- `"pin_channel"`: No clue what this is for.
- `"brightness"`: Adjust the brightness of the strip, up to 255.
- `"length"`: The number of LEDs on the pixel strip, including any that should always be off (see below).
- `"black"`: A list of ranges [start-end) corresonding to pixels that should always be black, such as around corners or tucked behind somewhere.

`"relay_remotes"` defines the remote controllers for relays. Each named remote has the following arguments:

- `"ip"`: The IP address to communcate over.
- `"port"`: Which port to connect to.
- `"relays"`: A 0-indexed list of the names of all relays connected. Pad with `null` if a relay is unused. Names should be globally unique.

`"relay_purposes"` groups relays into their logical uses. Each of the following should take a list, and all defined relays should ideally be in exactly one of these lists.

Name | Blank | Between shows | During Show | Night with no shows | Example |
------|-------|---------------|-------------|--------------------|--------|
`"off_when_blank"` | off | on | on | on | pixel strip power
`"off_for_shows"` | on | on | off | on | sign advertising the show
`"animate_between_shows"` | off | on | see "animations" | on | note, "on" is through animation
`"on_show_nights"` | off | on | on | off | speakers

## schedule

Schedule controls the time the the lights should turn on and off each evening.

Required arguments are `start_time` and `end_time`. Times can either be in a 24-hour `HH:MM` format, or `"sunset"`. If `"sunset"`, then `"sunset_offset"` is `HH:MM` offset from sunset time, with negative values representing time before sunset, and positive representing time after sunset. Sunset is calculated using `"location"`, which is a list of latitude and logitude in floating point format. For example, `[37.8, -122.4]` corresponds to San Francisco, CA.

## calendar

What animations happen on what days throughout the year.

Christmas comes but once a year, but holidays are year round! Specify `"start"` and `"end"` dates, and optional `"days"` of the week list to filter to certain days. Give it a name (used for debug output) and a list of what `"animations"` to play.

It may be necessary to specify multiple date ranges for an animation. For example, if Christmas animations should start playing the day after Thanksgiving, they will always play from November 30 through December 24, but could play as early as November 23 so long as that's a Friday, November 24 so long as that's a Friday or Saturday, and so on.

## animations

At this point, all animations run through the `image` module, but it is currently still required. Remind me to remove that requirement.

- `"shuffle"`: Whether the different songs should be shuffled, or played in the order defined here.
- `"countdown"`: Number of seconds between songs. Note that if >=3 seconds, "prepare_speakers.mp3" will be played at the beginning of the countdown.
- `"minute"`: At what minute of the hour the songs should start. If `null`, they will start as soon as loaded (useful for testing).
- `"days"`: List of which days of the week songs with music should play. On other days, only songs without music (not really songs...) will be played.
- `"songs"` gets its own section, below

### songs

Where all your hard work is defined! This is why you're here, and...I haven't written the readme yet. Good luck!