import time
reverse = True
NUM_LEDS = 77
leds = [0] * NUM_LEDS

pattern_size = 32
pattern = [
206,
160,
123,
90,
67,
47,
32,
20,
13,
8,
4,
2,
0,
0,
0,
0,
206,
160,
123,
90,
67,
47,
32,
20,
13,
8,
4,
2,
0,
0,
0,
0
]
if reverse: pattern.reverse()

i = 256
midpoint = 20
lit_leds = 60

while True:
    i = (i - 1) or 256
    for x in range(lit_leds//2):
        color = pattern[(x + i) % pattern_size]
        if (x and (midpoint + x < lit_leds)):
            leds[midpoint + x] = color
        if (x <= midpoint):
            leds[midpoint - x] = color
        else:
            leds[lit_leds + midpoint - x - 1] = color
    for led in leds:
        print(str(led).rjust(3), end='')
    print('\r', end='')
    time.sleep(1/24)