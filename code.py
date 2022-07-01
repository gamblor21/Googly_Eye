# SPDX-FileCopyrightText: 2022 Mark Komus
#
# SPDX-License-Identifier: MIT
#
# Inspired by work from Phil Burgess and Adafruit
# https://learn.adafruit.com/hallowing-googly-eye/
#
import time
import math
import board
import busio
import displayio
import vectorio
import gc9a01
import adafruit_lsm9ds1

# Release any resources currently in use for the displays
displayio.release_displays()

i2c = busio.I2C(board.IO6, board.IO5)
sensor = adafruit_lsm9ds1.LSM9DS1_I2C(i2c)

tft_clk = board.SCK
tft_mosi = board.IO35
tft_rst = board.IO38
tft_dc = board.IO9
tft_cs = board.IO8
spi = busio.SPI(clock=tft_clk, MOSI=tft_mosi)

# Make the displayio SPI bus and the GC9A01 display
display_bus = displayio.FourWire(
    spi, command=tft_dc, chip_select=tft_cs, reset=tft_rst, baudrate=80000000
)
display = gc9a01.GC9A01(display_bus, width=240, height=240)

# Create display group and add it to the display
group = displayio.Group()
display.show(group)

print("Starting")

palette = displayio.Palette(2)
palette[0] = 0xFFFFFF
palette[1] = 0x000000

EYE_RADUIS = 20

bg_circle = vectorio.Circle(pixel_shader=palette, radius=120, x=120, y=120, color_index=0)
group.append(bg_circle)

eye_circle = vectorio.Circle(pixel_shader=palette, radius=EYE_RADUIS, x=120, y=120, color_index=1)
group.append(eye_circle)

last_time = time.monotonic()
start_time = time.monotonic()

fps = 0
x = 0
y = 0
vx = 0
vy = 0

DRAG = 0.996
ELASTIC = 0.8
SCREEN_RADUIS = (120 - EYE_RADUIS) * (120 - EYE_RADUIS)

while True:
    now = time.monotonic()
    dt = now - last_time
    last_time = now

    ax, ay, az = sensor.acceleration
    ax = ax * dt
    ay = ay * dt
    vx = (vx - ay) * DRAG  # y direction is display x
    vy = (vy + ax) * DRAG

    new_x = x + vx
    new_y = y + vy

    d = new_x * new_x + new_y * new_y
    if d < SCREEN_RADUIS:
        x = new_x
        y = new_y
        eye_circle.x = int(x) + 120
        eye_circle.y = int(y) + 120
    else:
        vx = -vx * ELASTIC
        vy = -vy * ELASTIC
    fps += 1
    display.refresh()
    if fps % 500 == 0:
        dt = time.monotonic() - start_time
        print(fps, dt, fps / dt, end="")

        ax, ay, az = sensor.acceleration
        print(" ", ax, ay, az, x, vx, y, vy)
        print(spi.frequency)
        start_time = time.monotonic()
        fps = 0
