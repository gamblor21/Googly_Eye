# Googly_Eye
CircuitPython googly style eye for a circular display (GC9A01 driver) and a LSM9DS1 for the accelerometer.
The code should work on other displays if you swap out the driver for your driver and change the resolution
as required (it is still hard coded near the end).

If you wish to use more then one display at a time you will have to compile a custom version of
CircuitPython that increased max displays to two (or more). See:
https://todbot.com/blog/2022/05/19/multiple-displays-in-circuitpython-compiling-custom-circuitpython/
