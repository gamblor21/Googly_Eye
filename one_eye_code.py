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

G_SCALE = 2     # Change the acceleration speed for looks
DRAG = 0.996    # Represents friction on the surface lower value = slower
ELASTIC = 0.80  # Energy we lose bouncing on the edges

SCREEN_RADIUS = 120
EYE_RADIUS = 30
EYE_RADIUS2 = EYE_RADIUS * EYE_RADIUS
INNER_RADIUS = SCREEN_RADIUS - EYE_RADIUS
INNER_RADIUS2 = INNER_RADIUS * INNER_RADIUS

# Release any resources currently in use for the displays
displayio.release_displays()

# LSM9DS1 sensor
i2c = busio.I2C(board.IO6, board.IO5)
sensor = adafruit_lsm9ds1.LSM9DS1_I2C(i2c)

# Set up the display
tft_clk = board.SCK
tft_mosi = board.IO35
tft_rst = board.IO38
tft_dc = board.IO9
tft_cs = board.IO8
spi = busio.SPI(clock=tft_clk, MOSI=tft_mosi)

# Make the displayio SPI bus and the GC9A01 display
display_bus = displayio.FourWire(spi, command=tft_dc, chip_select=tft_cs, reset=tft_rst, baudrate=80000000)
display = gc9a01.GC9A01(display_bus, width=240, height=240, auto_refresh=False)

# Create display group and add it to the display
group = displayio.Group()
display.show(group)

print("Starting")

palette = displayio.Palette(2)
palette[0] = 0xFFFFFF   # background
palette[1] = 0x000000   # eye color

bg_circle = vectorio.Circle(pixel_shader=palette, radius=SCREEN_RADIUS, x=120, y=120, color_index=0)
group.append(bg_circle)

eye_circle = vectorio.Circle(pixel_shader=palette, radius=EYE_RADIUS, x=120, y=120, color_index=1)
group.append(eye_circle)

last_time = time.monotonic()

# Used to track FPS
start_time = time.monotonic()
fps = 0
skipped = 0

# Eye ball location x=0/y=0 is middle of the display
# vx/vy is the current velocity
x = 0
y = 0
vx = 0.0
vy = 0.0


while True:
    now = time.monotonic()
    dt = now - last_time
    last_time = now

    ax, ay, az = sensor.acceleration
    ax = ax * dt * G_SCALE
    ay = ay * dt * G_SCALE
    vx = (vx - ay) * DRAG  # y direction is display -x
    vy = (vy + ax) * DRAG  # x direction is display +y

    # runaway velocity check
    v = vx*vx + vy*vy
    if v > EYE_RADIUS2:
        v = EYE_RADIUS / math.sqrt(v)
        vx *= v
        vy *= v

    # this is where the eye should move to
    new_x = x + vx
    new_y = y + vy

    # But check if the eye will pass the screen border
    d = new_x * new_x + new_y * new_y
    if d > INNER_RADIUS2:
        #
        # This is the math from the the Hallowing example that is "hard"
        # The original code in Arduino has a lot of good comments

        # Find the vector from current to new position that crosses screen border
        dx = new_x - x
        dy = new_y - y

        # find intersection point from the vector to the circle (screen)
        n1 = n2 = 0.0
        x2 = x*x
        y2 = y*y
        a2 = dx*dx
        b2 = dy*dy
        a2b2 = a2 + b2
        n = a2*INNER_RADIUS2 - a2*y2 + 2.0*dx*dy*x*y + b2*INNER_RADIUS2 - b2*x2
        if n > 0.0 and a2b2 > 0.0:
            n = math.sqrt(n)
            n1 = (n - dx * x - dy * y) / a2b2
            n2 = -(n + dx * x + dy * y) / a2b2
        # use larger intersection point (there are two)
        if n2 > n1:
            n1 = n2

        # The single intersection point of movement vector and circle
        # That is where the eye will hit the circle
        ix = x + dx * n1
        iy = y + dy * n1

        # Calculate the bounce from the edge, which is the remainder of our velocity
        # and the opposite angle at which we intersected the circle
        mag1 = math.sqrt(dx*dx + dy*dy)
        dx1 = ix - x # vector from prior pos
        dy1 = iy - y # to edge of circle
        mag2 = math.sqrt(dx1*dx1 + dy1*dy1) # mag of that previous vector

        # Lose some energy in the bounce
        mag3 = (mag1 - mag2) * ELASTIC

        ax = -ix / INNER_RADIUS
        ay = -iy / INNER_RADIUS
        rx = ry = 0.0
        if mag1 > 0.0:
            rx = -dx / mag1
            ry = -dy / mag1

        dot = rx * ax + ry * ay
        rpx = ax * dot
        rpy = ay * dot
        rx += (rpx - rx) * 2.0  # reversed vector leaving the circle
        ry += (rpy - ry) * 2.0

        # New position is where we hit the circle plus the reflected vector
        # scaled down by mag3 (which lowers velocity due to bounce)
        new_x = ix + rx * mag3
        new_y = iy + ry * mag3

        # Set our new velocity values for the next move
        mag1 *= ELASTIC
        vx = rx * mag1
        vy = ry * mag1

    x = new_x
    y = new_y
    eye_circle.x = int(x) + 120
    eye_circle.y = int(y) + 120


    # experimental code to set a limit of FPS will skip frames if we are falling below this
    #if display.refresh(target_frames_per_second=120) is False:
        #skipped += 1
    #else:
        #fps +=1

    fps += 1
    display.refresh()

    # Every 500 frames print some information
    if fps % 500 == 0:
        dt = time.monotonic() - start_time
        print(fps / dt, skipped/dt, end="")

        ax, ay, az = sensor.acceleration
        print(" ", ax, ay, az, x, vx, y, vy)
        start_time = time.monotonic()
        fps = 0
        skipped = 0
