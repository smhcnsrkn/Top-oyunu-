# -*- coding: utf-8 -*-
"""
Top Sektirme Oyunu - Kenar Tehlike Bolgeleri ve Can Sistemi
Python + Kivy | Pydroid 3 / Android uyumlu | Tek dosya main.py
Harici asset/gorsel kullanilmaz.
"""

import math
import random

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.graphics import Color, Ellipse, Rectangle, Line, PushMatrix, PopMatrix, Rotate
from kivy.clock import Clock

# ---------------------------------------------------------------
# AYARLAR
# ---------------------------------------------------------------
BALL_SIZE = 40.0
BALL_RADIUS = BALL_SIZE / 2.0

DANGER_LINE_LEN = 40.0
DANGER_GAP = 240.0
DANGER_THICKNESS = 10.0

BASE_SPEED = 520.0
MAX_SPEED = 2000.0
SPEED_MULTIPLIER = 1.3

HEART_SIZE = 28.0
HEART_GAP = 8.0
HEART_FULL_COLOR = (0.95, 0.1, 0.15, 1)
HEART_EMPTY_COLOR = (0.25, 0.25, 0.25, 1)

HIT_PAUSE_DURATION = 0.5      # can kaybi sonrasi kisa bekleme (cooldown)
EFFECT_DURATION = 0.4         # carpma efekti suresi
MESSAGE_DURATION = 1.0        # "CARPTI" mesaji suresi

START_LIVES = 3


def circle_rect_collision(cx, cy, r, rx, ry, rw, rh):
    """Dairenin (top) dikdortgen (tehlike bolgesi) ile gercek temasini kontrol eder."""
    closest_x = max(rx, min(cx, rx + rw))
    closest_y = max(ry, min(cy, ry + rh))
    dx = cx - closest_x
    dy = cy - closest_y
    return (dx * dx + dy * dy) <= (r * r), closest_x, closest_y


class GameWidget(Widget):
    def __init__(self, **kwargs):
        super(GameWidget, self).__init__(**kwargs)

        # --- durum degiskenleri ---
        self.state = "playing"          # "playing" | "hit_pause" | "gameover"
        self.lives = START_LIVES
        self.current_speed = BASE_SPEED

        self.ball_x = 0.0
        self.ball_y = 0.0
        self.vx = 0.0
        self.vy = 0.0
        self._saved_vx = 0.0
        self._saved_vy = 0.0

        self.pause_until = 0.0
        self.effect_time = -999.0
        self.effect_pos = (0.0, 0.0)
        self.message_time = -999.0

        self.danger_rects = []          # her biri (x, y, w, h)
        self._zones_ready = False

        # --- UI elemanlari (canvas disi Label'lar) ---
        self.message_label = Label(
            text="", font_size="20sp", color=(1, 1, 1, 1),
            size_hint=(None, None), size=(400, 40)
        )
        self.add_widget(self.message_label)

        self.gameover_label = Label(
            text="", font_size="64sp", bold=True, color=(1, 0.08, 0.08, 1),
            size_hint=(None, None), size=(600, 140),
            halign="center", valign="middle"
        )
        self.gameover_label.bind(size=self.gameover_label.setter("text_size"))
        self.add_widget(self.gameover_label)

        self.restart_label = Label(
            text="", font_size="18sp", color=(1, 1, 1, 1),
            size_hint=(None, None), size=(500, 40),
            halign="center", valign="middle"
        )
        self.restart_label.bind(size=self.restart_label.setter("text_size"))
        self.add_widget(self.restart_label)

        self.bind(size=self._on_size_change, pos=self._on_size_change)

        Clock.schedule_once(self._init_after_layout, 0)

        Clock.schedule_interval(self.update, 1.0 / 60.0)

    def _init_after_layout(self, dt):
        if self.width > 0 and self.height > 0:
            self.generate_danger_zones()
            self.reset_ball(random_direction=True)
            self._zones_ready = True
        else:
            Clock.schedule_once(self._init_after_layout, 0)

    def _on_size_change(self, *args):
        if self.width > 0 and self.height > 0:
            self.generate_danger_zones()
            if not self._zones_ready:
                self.reset_ball(random_direction=True)
                self._zones_ready = True
            else:
                self.ball_x = min(self.ball_x, self.width - BALL_SIZE)
                self.ball_y = min(self.ball_y, self.height - BALL_SIZE)

    def generate_danger_zones(self):
        w = self.width
        h = self.height
        if w <= 0 or h <= 0:
            return

        rects = []

        x = 0.0
        while x + DANGER_LINE_LEN <= w:
            rects.append((x, h - DANGER_THICKNESS, DANGER_LINE_LEN, DANGER_THICKNESS))
            rects.append((x, 0.0, DANGER_LINE_LEN, DANGER_THICKNESS))
            x += DANGER_GAP

        y = 0.0
        while y + DANGER_LINE_LEN <= h:
            rects.append((0.0, y, DANGER_THICKNESS, DANGER_LINE_LEN))
            rects.append((w - DANGER_THICKNESS, y, DANGER_THICKNESS, DANGER_LINE_LEN))
            y += DANGER_GAP

        self.danger_rects = rects

    def reset_ball(self, random_direction=False):
        self.ball_x = (self.width - BALL_SIZE) / 2.0
        self.ball_y = (self.height - BALL_SIZE) / 2.0
        self.current_speed = BASE_SPEED

        if random_direction or self.vx == 0 or self.vy == 0:
            angle = random.uniform(0.3, 1.2)
            sx = random.choice([-1, 1])
            sy = random.choice([-1, 1])
            self.vx = sx * self.current_speed * math.cos(angle)
            self.vy = sy * self.current_speed * math.sin(angle)
        else:
            ang = math.atan2(self.vy, self.vx)
            self.vx = self.current_speed * math.cos(ang)
            self.vy = self.current_speed * math.sin(ang)

    def start_new_game(self):
        self.lives = START_LIVES
        self.state = "playing"
        self.effect_time = -999.0
        self.message_time = -999.0
        self.message_label.text = ""
        self.gameover_label.text = ""
        self.restart_label.text = ""
        self.pause_until = 0.0
        self.reset_ball(random_direction=True)

    def process_hit(self, hit_point):
        now = Clock.get_boottime()
        self.lives -= 1

        self.effect_pos = hit_point
        self.effect_time = now
        self.message_time = now

        if self.lives <= 0:
            self.lives = 0
            self.state = "gameover"
            self.vx = 0.0
            self.vy = 0.0
            self.gameover_label.text = "GAME OVER"
            self.restart_label.text = "Yeniden baslamak icin ekrana dokun"
        else:
            self._saved_vx = self.vx
            self._saved_vy = self.vy
            self.vx = 0.0
            self.vy = 0.0
            self.ball_x = (self.width - BALL_SIZE) / 2.0
            self.ball_y = (self.height - BALL_SIZE) / 2.0
            self.state = "hit_pause"
            self.pause_until = now + HIT_PAUSE_DURATION

    def update(self, dt):
        if not self._zones_ready:
            return

        now = Clock.get_boottime()

        if self.state == "hit_pause":
            if now >= self.pause_until:
                self.vx = self._saved_vx
                self.vy = self._saved_vy
                self.state = "playing"

        elif self.state == "playing":
            self._update_physics(dt)

        self._update_ui(now)
        self.redraw()

    def _update_physics(self, dt):
        w, h = self.width, self.height

        self.ball_x += self.vx * dt
        self.ball_y += self.vy * dt

        touching_left = self.ball_x <= 0
        touching_right = (self.ball_x + BALL_SIZE) >= w
        touching_bottom = self.ball_y <= 0
        touching_top = (self.ball_y + BALL_SIZE) >= h

        if self.ball_x < 0:
            self.ball_x = 0
        if self.ball_x + BALL_SIZE > w:
            self.ball_x = w - BALL_SIZE
        if self.ball_y < 0:
            self.ball_y = 0
        if self.ball_y + BALL_SIZE > h:
            self.ball_y = h - BALL_SIZE

        if touching_left or touching_right or touching_bottom or touching_top:
            cx = self.ball_x + BALL_RADIUS
            cy = self.ball_y + BALL_RADIUS

            hit_rect = None
            hit_point = None
            for (rx, ry, rw, rh) in self.danger_rects:
                collided, px, py = circle_rect_collision(cx, cy, BALL_RADIUS, rx, ry, rw, rh)
                if collided:
                    hit_rect = (rx, ry, rw, rh)
                    hit_point = (px, py)
                    break

            if hit_rect is not None:
                self.process_hit(hit_point)
                return

            if touching_left:
                self.vx = abs(self.vx)
            if touching_right:
                self.vx = -abs(self.vx)
            if touching_bottom:
                self.vy = abs(self.vy)
            if touching_top:
                self.vy = -abs(self.vy)

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return super(GameWidget, self).on_touch_down(touch)

        if self.state == "gameover":
            self.start_new_game()
            return True

        if self.state == "playing":
            cx = self.ball_x + BALL_RADIUS
            cy = self.ball_y + BALL_RADIUS
            dx = touch.x - cx
            dy = touch.y - cy
            dist = math.hypot(dx, dy)
            if dist == 0:
                dx, dy, dist = 1.0, 1.0, math.sqrt(2)

            ux, uy = dx / dist, dy / dist

            self.current_speed = min(self.current_speed * SPEED_MULTIPLIER, MAX_SPEED)
            self.vx = ux * self.current_speed
            self.vy = uy * self.current_speed

        return True

    def _update_ui(self, now):
        if now - self.message_time <= MESSAGE_DURATION:
            self.message_label.text = "\U0001F4A5 CARPTI! -1 CAN"
        else:
            self.message_label.text = ""
        self.message_label.pos = ((self.width - self.message_label.width) / 2.0, self.height - 45)

        self.gameover_label.pos = ((self.width - self.gameover_label.width) / 2.0,
                                    (self.height - self.gameover_label.height) / 2.0 + 20)
        self.restart_label.pos = ((self.width - self.restart_label.width) / 2.0,
                                   (self.height - self.restart_label.height) / 2.0 - 40)

    def draw_heart(self, x, y, size, color):
        r = size / 4.0
        with self.canvas:
            Color(*color)
            Ellipse(pos=(x, y + r), size=(2 * r, 2 * r))
            Ellipse(pos=(x + 2 * r, y + r), size=(2 * r, 2 * r))
            PushMatrix()
            Rotate(angle=45, origin=(x + 2 * r, y + r))
            Rectangle(pos=(x + 2 * r - r, y + r - r), size=(2 * r, 2 * r))
            PopMatrix()

    def draw_hearts(self):
        start_x = 12.0
        top_y = self.height - HEART_SIZE - 10.0
        for i in range(START_LIVES):
            hx = start_x + i * (HEART_SIZE + HEART_GAP)
            color = HEART_FULL_COLOR if i < self.lives else HEART_EMPTY_COLOR
            self.draw_heart(hx, top_y, HEART_SIZE, color)

    def redraw(self):
        self.canvas.clear()
        with self.canvas:
            Color(1, 0, 0, 1)
            for (rx, ry, rw, rh) in self.danger_rects:
                Rectangle(pos=(rx, ry), size=(rw, rh))

        self.draw_hearts()

        with self.canvas:
            if self.state != "gameover" or self.lives == 0:
                Color(1, 0, 0, 1)
                Ellipse(pos=(self.ball_x, self.ball_y), size=(BALL_SIZE, BALL_SIZE))

            now = Clock.get_boottime()
            elapsed = now - self.effect_time
            if 0 <= elapsed <= EFFECT_DURATION:
                progress = elapsed / EFFECT_DURATION
                alpha = max(0.0, 1.0 - progress)
                ring_radius = 10 + progress * 60
                ex, ey = self.effect_pos

                Color(1, 1, 1, alpha)
                Ellipse(pos=(ex - 12, ey - 12), size=(24, 24))

                Color(1, 0, 0, alpha)
                Line(circle=(ex, ey, ring_radius), width=2)

            if self.state == "gameover":
                Color(0, 0, 0, 0.65)
                Rectangle(pos=(0, 0), size=(self.width, self.height))

        for child in reversed(self.children):
            self.canvas.add(child.canvas)


class BallGameApp(App):
    def build(self):
        return GameWidget()


if __name__ == "__main__":
    BallGameApp().run()
