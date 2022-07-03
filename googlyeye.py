import time
import math

class GooglyEye:
    def __init__(self, x=0, y=0, drag=0.996, g_scale=2, eye_radius=30, screen_radius=120, elastic=0.80):
        # Eye ball location x=0/y=0 is middle of the display
        # vx/vy is the current velocity
        self.x = 0
        self.y = 0
        self.vx = 0.0
        self.vy = 0.0
        self.last_update = time.monotonic()
        self.drag = drag
        self.g_scale = g_scale
        self.eye_radius = eye_radius
        self._eye_radius2 = eye_radius * eye_radius
        self.screen_radius = screen_radius
        self._screen_radius2 = screen_radius * screen_radius
        self._inner_radius = screen_radius - eye_radius
        self._inner_radius2 = self._inner_radius * self._inner_radius
        self.elastic = elastic

    def update(self, ax, ay):
        now = time.monotonic()
        dt = now - self.last_update
        self.last_update = now

        ax = ax * dt * self.g_scale
        ay = ay * dt * self.g_scale
        self.vx = (self.vx - ay) * self.drag  # y direction is display -x
        self.vy = (self.vy + ax) * self.drag  # x direction is display +y

        # runaway velocity check
        v = self.vx*self.vx + self.vy*self.vy
        if v > self._eye_radius2:
            v = self.eye_radius / math.sqrt(v)
            self.vx *= v
            self.vy *= v

        # this is where the eye should move to
        new_x = self.x + self.vx
        new_y = self.y + self.vy

        # But check if the eye will pass the screen border
        d = new_x * new_x + new_y * new_y
        if d > self._inner_radius2:
            #
            # This is the math from the the Hallowing example that is "hard"
            # The original code in Arduino has a lot of good comments

            # Find the vector from current to new position that crosses screen border
            dx = new_x - self.x
            dy = new_y - self.y

            # find intersection point from the vector to the circle (screen)
            n1 = n2 = 0.0
            x2 = self.x*self.x
            y2 = self.y*self.y
            a2 = dx*dx
            b2 = dy*dy
            a2b2 = a2 + b2
            n = a2*self._inner_radius2 - a2*y2 + 2.0*dx*dy*self.x*self.y + b2*self._inner_radius2 - b2*x2
            if n > 0.0 and a2b2 > 0.0:
                n = math.sqrt(n)
                n1 = (n - dx * self.x - dy * self.y) / a2b2
                n2 = -(n + dx * self.x + dy * self.y) / a2b2
            # use larger intersection point (there are two)
            if n2 > n1:
                n1 = n2

            # The single intersection point of movement vector and circle
            # That is where the eye will hit the circle
            ix = self.x + dx * n1
            iy = self.y + dy * n1

            # Calculate the bounce from the edge, which is the remainder of our velocity
            # and the opposite angle at which we intersected the circle
            mag1 = math.sqrt(dx*dx + dy*dy)
            dx1 = ix - self.x # vector from prior pos
            dy1 = iy - self.y # to edge of circle
            mag2 = math.sqrt(dx1*dx1 + dy1*dy1) # mag of that previous vector

            # Lose some energy in the bounce
            mag3 = (mag1 - mag2) * self.elastic

            ax = -ix / self._inner_radius
            ay = -iy / self._inner_radius
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
            mag1 *= self.elastic
            self.vx = rx * mag1
            self.vy = ry * mag1

        self.x = new_x
        self.y = new_y
