# SPDX-FileCopyrightText: 2022 Mark Komus
#
# SPDX-License-Identifier: MIT
#
# Inspired by work from Phil Burgess and Adafruit
# https://learn.adafruit.com/hallowing-googly-eye/
#
import time
import board
import busio
import displayio
import vectorio
import gc9a01
import adafruit_lsm9ds1
from googlyeye import GooglyEye

G_SCALE = 4     # Change the acceleration speed for looks
DRAG = 0.999    # Represents friction on the surface lower value = slower
ELASTIC = 0.80  # Energy we lose bouncing on the edges

SCREEN_RADIUS = 120
EYE_RADIUS = 30
EYE_RADIUS2 = EYE_RADIUS * EYE_RADIUS
INNER_RADIUS = SCREEN_RADIUS - EYE_RADIUS
INNER_RADIUS2 = INNER_RADIUS * INNER_RADIUS

# Release any resources currently in use for the displays
displayio.release_displays()

# LSM9DS1 sensor
i2c = busio.I2C(board.IO5, board.IO4)
sensor = adafruit_lsm9ds1.LSM9DS1_I2C(i2c)

# Set up the display
tft_clk = board.SCK
tft_mosi = board.IO35
tft_rst = board.IO38
tft_dc = board.IO9
tft_cs = board.IO8
spi_left = busio.SPI(clock=tft_clk, MOSI=tft_mosi)

tft_clk2 = board.IO6
tft_mosi2 = board.IO7
tft_rst2 = board.IO0
tft_dc2 = board.IO17
tft_cs2 = board.IO18
spi_right = busio.SPI(clock=tft_clk2, MOSI=tft_mosi2)

# Make the displayio SPI bus and the GC9A01 display
display_bus_left = displayio.FourWire(spi_left, command=tft_dc, chip_select=tft_cs, reset=tft_rst, baudrate=80000000)
display_left = gc9a01.GC9A01(display_bus_left, width=240, height=240, auto_refresh=False)

display_bus_right = displayio.FourWire(spi_right, command=tft_dc2, chip_select=tft_cs2, reset=tft_rst2, baudrate=80000000)
display_right = gc9a01.GC9A01(display_bus_right, width=240, height=240, auto_refresh=False)

# Create display group and add it to the display
group_left = displayio.Group()
group_right = displayio.Group()
display_left.show(group_left)
display_right.show(group_right)

print("Starting")

palette = displayio.Palette(2)
palette[0] = 0xFFFFFF   # background
palette[1] = 0x000000   # eye color

bg_circle_left = vectorio.Circle(pixel_shader=palette, radius=SCREEN_RADIUS, x=120, y=120, color_index=0)
group_left.append(bg_circle_left)

bg_circle_right = vectorio.Circle(pixel_shader=palette, radius=SCREEN_RADIUS, x=120, y=120, color_index=0)
group_right.append(bg_circle_right)

eye_circle_left = vectorio.Circle(pixel_shader=palette, radius=EYE_RADIUS, x=120, y=120, color_index=1)
group_left.append(eye_circle_left)

eye_circle_right = vectorio.Circle(pixel_shader=palette, radius=EYE_RADIUS, x=120, y=120, color_index=1)
group_right.append(eye_circle_right)

eye_left = GooglyEye()
eye_right = GooglyEye()

# Used to track FPS
start_time = time.monotonic()
fps = 0
skipped = 0

while True:
    ax, ay, az = sensor.acceleration
    eye_left.update(ax, ay)
    eye_circle_left.x = int(eye_left.x) + 120
    eye_circle_left.y = int(eye_left.y) + 120
    display_left.refresh()
    eye_right.update(ax, ay)
    eye_circle_right.x = int(eye_right.x) + 120
    eye_circle_right.y = int(eye_right.y) + 120
    display_right.refresh()

    # experimental code to set a limit of FPS will skip frames if we are falling below this
    #if display.refresh(target_frames_per_second=120) is False:
        #skipped += 1
    #else:
        #fps +=1

    fps += 1
    display_left.refresh()
    display_right.refresh()

    # Every 500 frames print some information
    if fps % 500 == 0:
        dt = time.monotonic() - start_time
        print(fps / dt, skipped/dt)
        start_time = time.monotonic()
        fps = 0
        skipped = 0
