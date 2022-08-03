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

EYE_RADIUS = 25
EYE_RADIUS2 = EYE_RADIUS * EYE_RADIUS

SCREEN_RADIUS = 120
INNER_RADIUS = SCREEN_RADIUS - EYE_RADIUS
INNER_RADIUS2 = INNER_RADIUS * INNER_RADIUS

# Release any resources currently in use for the displays
displayio.release_displays()

# LSM9DS1 sensor
i2c = busio.I2C(board.SCL, board.SDA)
sensor = adafruit_lsm9ds1.LSM9DS1_I2C(i2c)

# Set up the left display
tft_clk = board.SCK
tft_mosi = board.MOSI
tft_rst = board.D9
tft_dc = board.D10
tft_cs = board.RX
spi_left = busio.SPI(clock=tft_clk, MOSI=tft_mosi)

# Set up the right display
tft_clk2 = board.A0
tft_mosi2 = board.A1
tft_rst2 = board.D11
tft_dc2 = board.D12
tft_cs2 = board.A3
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

    # Orientate the sensor directions to the display directions
    eye_ax = -az
    eye_ay = -ax

    eye_left.update(eye_ax, eye_ay)
    eye_circle_left.x = int(eye_left.x) + SCREEN_RADIUS
    eye_circle_left.y = int(eye_left.y) + SCREEN_RADIUS
    display_left.refresh()

    eye_right.update(eye_ax, eye_ay)
    eye_circle_right.x = int(eye_right.x) + SCREEN_RADIUS
    eye_circle_right.y = int(eye_right.y) + SCREEN_RADIUS
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
        print("FPS:",fps / dt, skipped/dt)
        print("Left:",eye_left.x,eye_left.y,eye_left.vx,eye_left.vy)
        print("Rght:",eye_right.x,eye_right.y,eye_right.vx,eye_right.vy)
        start_time = time.monotonic()
        fps = 0
        skipped = 0