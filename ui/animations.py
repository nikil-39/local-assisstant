"""
Animations Module - Orb rendering, particle system, waveform visualization,
and state-driven animation controller for the Jarvis UI.

All painting uses QPainter for smooth, GPU-friendly rendering.
"""

import math
import random
from enum import Enum, auto

from PyQt6.QtCore import (
    Qt, QTimer, QPointF, QRectF, QPropertyAnimation,
    QEasingCurve, pyqtProperty, QObject, pyqtSignal,
)
from PyQt6.QtGui import (
    QPainter, QColor, QRadialGradient, QLinearGradient, QConicalGradient,
    QPen, QBrush, QPainterPath, QFont,
)
from PyQt6.QtWidgets import QWidget


# ═══════════════════════════════════════════════════════════════════════════
# State Definitions
# ═══════════════════════════════════════════════════════════════════════════

class AssistantState(Enum):
    IDLE = auto()
    LISTENING = auto()
    PROCESSING = auto()
    SPEAKING = auto()
    ERROR = auto()


# ═══════════════════════════════════════════════════════════════════════════
# Color Palette
# ═══════════════════════════════════════════════════════════════════════════

class Palette:
    PRIMARY = QColor("#6366f1")       # Indigo
    SECONDARY = QColor("#8b5cf6")     # Purple
    ACCENT = QColor("#06b6d4")        # Cyan
    BG_DARK = QColor(17, 24, 39)      # Near-black
    BG_CARD = QColor(30, 41, 59, 200) # Slate with alpha
    TEXT = QColor("#e2e8f0")          # Light slate
    TEXT_DIM = QColor("#94a3b8")      # Muted text
    SUCCESS = QColor("#22c55e")       # Green
    ERROR = QColor("#ef4444")         # Red
    WARNING = QColor("#f59e0b")       # Amber

    # State-specific colors
    IDLE_GLOW = QColor(99, 102, 241, 80)
    LISTEN_GLOW = QColor(6, 182, 212, 120)
    PROCESS_GLOW = QColor(139, 92, 246, 100)
    SPEAK_GLOW = QColor(99, 102, 241, 100)
    ERROR_GLOW = QColor(239, 68, 68, 80)


# ═══════════════════════════════════════════════════════════════════════════
# Particle System
# ═══════════════════════════════════════════════════════════════════════════

class Particle:
    __slots__ = ("x", "y", "vx", "vy", "size", "alpha", "life", "max_life", "color")

    def __init__(self, x: float, y: float, bounds_w: float, bounds_h: float):
        self.x = x
        self.y = y
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(0.15, 0.6)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.size = random.uniform(1.5, 4.0)
        self.alpha = random.uniform(0.2, 0.7)
        self.max_life = random.uniform(120, 300)
        self.life = self.max_life
        colors = [Palette.PRIMARY, Palette.SECONDARY, Palette.ACCENT]
        self.color = random.choice(colors)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 1
        self.alpha = max(0, (self.life / self.max_life) * 0.7)

    @property
    def alive(self) -> bool:
        return self.life > 0


class ParticleSystem:
    """Manages a collection of floating ambient particles."""

    def __init__(self, width: float, height: float, max_particles: int = 60):
        self.width = width
        self.height = height
        self.max_particles = max_particles
        self.particles: list[Particle] = []
        self.intensity = 1.0  # Multiplier for spawn rate

    def resize(self, width: float, height: float):
        self.width = width
        self.height = height

    def update(self):
        # Spawn new particles
        spawn_rate = max(1, int(self.intensity * 2))
        while len(self.particles) < self.max_particles:
            x = random.uniform(0, self.width)
            y = random.uniform(0, self.height)
            self.particles.append(Particle(x, y, self.width, self.height))
            spawn_rate -= 1
            if spawn_rate <= 0:
                break

        # Update existing
        for p in self.particles:
            p.update()

        # Remove dead particles
        self.particles = [p for p in self.particles if p.alive]

    def draw(self, painter: QPainter):
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        for p in self.particles:
            color = QColor(p.color)
            color.setAlphaF(p.alpha)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(color))
            painter.drawEllipse(QPointF(p.x, p.y), p.size, p.size)
        painter.restore()


# ═══════════════════════════════════════════════════════════════════════════
# Orb Widget - The central animated sphere
# ═══════════════════════════════════════════════════════════════════════════

class OrbWidget(QWidget):
    """Central animated orb with state-driven visual effects."""

    def __init__(self, parent=None, orb_size: int = 280):
        super().__init__(parent)
        self._orb_size = orb_size
        self._state = AssistantState.IDLE
        self._scale = 1.0
        self._rotation = 0.0
        self._glow_intensity = 0.5
        self._ring_rotation = 0.0
        self._pulse_phase = 0.0
        self._ripple_radius = 0.0
        self._ripple_alpha = 0.0
        self._audio_level = 0.0
        self._waveform_data: list[float] = [0.0] * 12

        # Animation timer - 60fps
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)
        self._timer.start(16)  # ~60fps

        # Pulse animation
        self._pulse_anim = QPropertyAnimation(self, b"pulse_phase")
        self._pulse_anim.setDuration(3000)
        self._pulse_anim.setStartValue(0.0)
        self._pulse_anim.setEndValue(2 * math.pi)
        self._pulse_anim.setLoopCount(-1)
        self._pulse_anim.setEasingCurve(QEasingCurve.Type.Linear)
        self._pulse_anim.start()

        self.setMinimumSize(orb_size + 100, orb_size + 100)

    # ── Properties for QPropertyAnimation ──────────────────────────────

    @pyqtProperty(float)
    def scale(self):
        return self._scale

    @scale.setter
    def scale(self, val):
        self._scale = val
        self.update()

    @pyqtProperty(float)
    def pulse_phase(self):
        return self._pulse_phase

    @pulse_phase.setter
    def pulse_phase(self, val):
        self._pulse_phase = val

    @pyqtProperty(float)
    def glow_intensity(self):
        return self._glow_intensity

    @glow_intensity.setter
    def glow_intensity(self, val):
        self._glow_intensity = val
        self.update()

    @pyqtProperty(float)
    def ripple_radius(self):
        return self._ripple_radius

    @ripple_radius.setter
    def ripple_radius(self, val):
        self._ripple_radius = val

    @pyqtProperty(float)
    def ripple_alpha(self):
        return self._ripple_alpha

    @ripple_alpha.setter
    def ripple_alpha(self, val):
        self._ripple_alpha = val

    # ── State Management ──────────────────────────────────────────────

    def set_state(self, state: AssistantState):
        self._state = state
        self._transition_to_state(state)

    def set_audio_level(self, level: float):
        self._audio_level = level
        # Update waveform data with smoothing
        self._waveform_data.pop(0)
        self._waveform_data.append(level)

    def _transition_to_state(self, state: AssistantState):
        """Animate transition to a new state."""
        if state == AssistantState.IDLE:
            self._animate_to_idle()
        elif state == AssistantState.LISTENING:
            self._animate_to_listening()
        elif state == AssistantState.PROCESSING:
            self._animate_to_processing()
        elif state == AssistantState.SPEAKING:
            self._animate_to_speaking()
        elif state == AssistantState.ERROR:
            self._animate_to_error()

    def _animate_to_idle(self):
        anim = QPropertyAnimation(self, b"scale")
        anim.setDuration(500)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)

        glow_anim = QPropertyAnimation(self, b"glow_intensity")
        glow_anim.setDuration(500)
        glow_anim.setEndValue(0.5)
        glow_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        glow_anim.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)

    def _animate_to_listening(self):
        anim = QPropertyAnimation(self, b"scale")
        anim.setDuration(400)
        anim.setEndValue(1.08)
        anim.setEasingCurve(QEasingCurve.Type.OutBack)
        anim.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)

        glow_anim = QPropertyAnimation(self, b"glow_intensity")
        glow_anim.setDuration(400)
        glow_anim.setEndValue(0.9)
        glow_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        glow_anim.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)

    def _animate_to_processing(self):
        anim = QPropertyAnimation(self, b"scale")
        anim.setDuration(300)
        anim.setEndValue(1.03)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)

        glow_anim = QPropertyAnimation(self, b"glow_intensity")
        glow_anim.setDuration(300)
        glow_anim.setEndValue(0.7)
        glow_anim.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)

    def _animate_to_speaking(self):
        # Trigger ripple effect
        ripple = QPropertyAnimation(self, b"ripple_radius")
        ripple.setDuration(1000)
        ripple.setStartValue(0.0)
        ripple.setEndValue(float(self._orb_size))
        ripple.setEasingCurve(QEasingCurve.Type.OutQuad)
        ripple.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)

        alpha = QPropertyAnimation(self, b"ripple_alpha")
        alpha.setDuration(1000)
        alpha.setStartValue(0.6)
        alpha.setEndValue(0.0)
        alpha.setEasingCurve(QEasingCurve.Type.OutQuad)
        alpha.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)

        glow_anim = QPropertyAnimation(self, b"glow_intensity")
        glow_anim.setDuration(300)
        glow_anim.setEndValue(0.8)
        glow_anim.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)

    def _animate_to_error(self):
        anim = QPropertyAnimation(self, b"scale")
        anim.setDuration(200)
        anim.setEndValue(0.95)
        anim.setEasingCurve(QEasingCurve.Type.OutBounce)
        anim.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)

    # ── Animation Loop ────────────────────────────────────────────────

    def _animate(self):
        """Called every frame (~60fps)."""
        # Ring rotation
        if self._state == AssistantState.PROCESSING:
            self._ring_rotation += 3.0
        elif self._state == AssistantState.LISTENING:
            self._ring_rotation += 1.0
        else:
            self._ring_rotation += 0.3

        if self._ring_rotation >= 360:
            self._ring_rotation -= 360

        # Idle pulse
        if self._state == AssistantState.IDLE:
            pulse = 1.0 + 0.03 * math.sin(self._pulse_phase)
            self._scale = pulse

        self.update()

    # ── Painting ──────────────────────────────────────────────────────

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        cx = self.width() / 2
        cy = self.height() / 2
        r = self._orb_size / 2

        # Draw concentric rings
        self._draw_rings(painter, cx, cy, r)

        # Draw outer glow
        self._draw_glow(painter, cx, cy, r)

        # Draw main orb
        self._draw_orb(painter, cx, cy, r)

        # Draw inner highlight
        self._draw_highlight(painter, cx, cy, r)

        # Draw state-specific effects
        if self._state == AssistantState.LISTENING:
            self._draw_audio_bars(painter, cx, cy, r)
        elif self._state == AssistantState.PROCESSING:
            self._draw_processing_arc(painter, cx, cy, r)
        elif self._state == AssistantState.SPEAKING:
            self._draw_ripple(painter, cx, cy)

        # Draw status indicator
        self._draw_status_dot(painter, cx, cy, r)

        painter.end()

    def _draw_glow(self, painter: QPainter, cx: float, cy: float, r: float):
        """Draw the outer glow around the orb."""
        painter.save()
        glow_r = r * self._scale * 1.5

        state_colors = {
            AssistantState.IDLE: Palette.IDLE_GLOW,
            AssistantState.LISTENING: Palette.LISTEN_GLOW,
            AssistantState.PROCESSING: Palette.PROCESS_GLOW,
            AssistantState.SPEAKING: Palette.SPEAK_GLOW,
            AssistantState.ERROR: Palette.ERROR_GLOW,
        }
        glow_color = state_colors.get(self._state, Palette.IDLE_GLOW)

        gradient = QRadialGradient(cx, cy, glow_r)
        inner_color = QColor(glow_color)
        inner_color.setAlphaF(self._glow_intensity * 0.5)
        gradient.setColorAt(0.0, inner_color)
        gradient.setColorAt(0.5, QColor(glow_color.red(), glow_color.green(), glow_color.blue(), 30))
        gradient.setColorAt(1.0, QColor(0, 0, 0, 0))

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(gradient))
        painter.drawEllipse(QPointF(cx, cy), glow_r, glow_r)
        painter.restore()

    def _draw_orb(self, painter: QPainter, cx: float, cy: float, r: float):
        """Draw the main orb sphere with gradient."""
        painter.save()
        orb_r = r * self._scale

        # Main gradient
        gradient = QRadialGradient(cx - orb_r * 0.25, cy - orb_r * 0.25, orb_r * 1.2)
        gradient.setColorAt(0.0, QColor(120, 130, 255, 240))   # Light center
        gradient.setColorAt(0.3, Palette.PRIMARY)
        gradient.setColorAt(0.6, Palette.SECONDARY)
        gradient.setColorAt(1.0, QColor(50, 30, 120, 200))     # Dark edge

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(gradient))
        painter.drawEllipse(QPointF(cx, cy), orb_r, orb_r)

        # Subtle border
        border_pen = QPen(QColor(120, 130, 255, 60))
        border_pen.setWidthF(1.5)
        painter.setPen(border_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QPointF(cx, cy), orb_r, orb_r)
        painter.restore()

    def _draw_highlight(self, painter: QPainter, cx: float, cy: float, r: float):
        """Draw the glossy highlight on top of the orb."""
        painter.save()
        orb_r = r * self._scale
        highlight_r = orb_r * 0.7

        gradient = QRadialGradient(cx - orb_r * 0.2, cy - orb_r * 0.3, highlight_r)
        gradient.setColorAt(0.0, QColor(255, 255, 255, 50))
        gradient.setColorAt(0.5, QColor(255, 255, 255, 15))
        gradient.setColorAt(1.0, QColor(255, 255, 255, 0))

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(gradient))
        painter.drawEllipse(QPointF(cx - orb_r * 0.1, cy - orb_r * 0.2), highlight_r, highlight_r * 0.6)
        painter.restore()

    def _draw_rings(self, painter: QPainter, cx: float, cy: float, r: float):
        """Draw animated concentric rings around the orb."""
        painter.save()
        painter.translate(cx, cy)

        ring_configs = [
            (r * 1.15, 1.5, 0.20, 0),
            (r * 1.30, 1.0, 0.12, 120),
            (r * 1.45, 0.8, 0.08, 240),
        ]

        for ring_r, width, alpha, offset in ring_configs:
            rotation = self._ring_rotation + offset
            painter.save()
            painter.rotate(rotation)

            color = QColor(Palette.ACCENT)
            color.setAlphaF(alpha * self._glow_intensity)
            pen = QPen(color)
            pen.setWidthF(width)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)

            # Draw dashed arc segments
            rect = QRectF(-ring_r, -ring_r, ring_r * 2, ring_r * 2)
            painter.drawArc(rect, 0, 2880)       # 0 to 180 degrees (in 1/16th)
            painter.drawArc(rect, 3600, 1440)     # 225 to 315 degrees

            painter.restore()

        painter.restore()

    def _draw_audio_bars(self, painter: QPainter, cx: float, cy: float, r: float):
        """Draw audio-reactive bars around the orb when listening."""
        painter.save()
        bar_count = 12
        orb_r = r * self._scale

        for i in range(bar_count):
            angle_deg = (360 / bar_count) * i
            angle_rad = math.radians(angle_deg)

            # Use waveform data with some randomness for visual interest
            data_idx = i % len(self._waveform_data)
            level = self._waveform_data[data_idx]
            level = max(0.1, level + random.uniform(-0.05, 0.05))

            bar_length = 15 + level * 45
            bar_width = 4

            # Starting point on orb edge
            sx = cx + math.cos(angle_rad) * (orb_r + 8)
            sy = cy + math.sin(angle_rad) * (orb_r + 8)

            # End point
            ex = cx + math.cos(angle_rad) * (orb_r + 8 + bar_length)
            ey = cy + math.sin(angle_rad) * (orb_r + 8 + bar_length)

            # Color gradient based on level
            color = QColor(Palette.ACCENT)
            color.setAlphaF(0.4 + level * 0.5)
            pen = QPen(color)
            pen.setWidthF(bar_width)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            painter.drawLine(QPointF(sx, sy), QPointF(ex, ey))

        painter.restore()

    def _draw_processing_arc(self, painter: QPainter, cx: float, cy: float, r: float):
        """Draw spinning arc during processing."""
        painter.save()
        orb_r = r * self._scale + 10

        color = QColor(Palette.ACCENT)
        color.setAlphaF(0.7)
        pen = QPen(color)
        pen.setWidthF(3)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        rect = QRectF(cx - orb_r, cy - orb_r, orb_r * 2, orb_r * 2)
        start_angle = int(self._ring_rotation * 16)
        span_angle = 90 * 16
        painter.drawArc(rect, start_angle, span_angle)

        # Second arc opposite
        painter.drawArc(rect, start_angle + 180 * 16, span_angle)
        painter.restore()

    def _draw_ripple(self, painter: QPainter, cx: float, cy: float):
        """Draw ripple effect during speaking."""
        if self._ripple_alpha <= 0:
            return
        painter.save()
        color = QColor(Palette.ACCENT)
        color.setAlphaF(self._ripple_alpha)
        pen = QPen(color)
        pen.setWidthF(2)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QPointF(cx, cy), self._ripple_radius, self._ripple_radius)
        painter.restore()

    def _draw_status_dot(self, painter: QPainter, cx: float, cy: float, r: float):
        """Draw a small status indicator dot below the orb."""
        painter.save()
        dot_y = cy + r * self._scale + 25
        dot_r = 4

        state_colors = {
            AssistantState.IDLE: Palette.TEXT_DIM,
            AssistantState.LISTENING: Palette.ACCENT,
            AssistantState.PROCESSING: Palette.WARNING,
            AssistantState.SPEAKING: Palette.SUCCESS,
            AssistantState.ERROR: Palette.ERROR,
        }
        color = state_colors.get(self._state, Palette.TEXT_DIM)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(color))
        painter.drawEllipse(QPointF(cx, dot_y), dot_r, dot_r)
        painter.restore()


# ═══════════════════════════════════════════════════════════════════════════
# Waveform Visualization Widget
# ═══════════════════════════════════════════════════════════════════════════

class WaveformWidget(QWidget):
    """Horizontal audio waveform bar visualization at the bottom."""

    def __init__(self, parent=None, bar_count: int = 40):
        super().__init__(parent)
        self.bar_count = bar_count
        self._levels: list[float] = [0.0] * bar_count
        self._target_levels: list[float] = [0.0] * bar_count
        self._active = False
        self.setFixedHeight(50)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._smooth_update)
        self._timer.start(33)  # ~30fps

    def set_level(self, level: float):
        """Update waveform with a new audio level."""
        self._active = True
        # Shift and add new level with some variation
        self._target_levels.pop(0)
        self._target_levels.append(level)

        # Add organic variation to nearby bars
        for i in range(self.bar_count):
            base = self._target_levels[i]
            variation = random.uniform(-0.1, 0.1) * level
            self._target_levels[i] = max(0, min(1, base + variation))

    def set_idle(self):
        """Return to idle state."""
        self._active = False
        self._target_levels = [0.0] * self.bar_count

    def _smooth_update(self):
        """Smoothly interpolate towards target levels."""
        changed = False
        for i in range(self.bar_count):
            diff = self._target_levels[i] - self._levels[i]
            if abs(diff) > 0.001:
                self._levels[i] += diff * 0.3
                changed = True
            elif not self._active:
                self._levels[i] *= 0.9
                if self._levels[i] > 0.001:
                    changed = True

        if changed:
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        bar_width = max(2, (w / self.bar_count) * 0.6)
        gap = (w / self.bar_count) * 0.4
        total_bar = bar_width + gap

        center_y = h / 2

        for i in range(self.bar_count):
            level = self._levels[i]
            bar_height = max(2, level * (h * 0.8))

            x = i * total_bar + gap / 2

            # Gradient color based on position
            t = i / self.bar_count
            color = QColor()
            color.setRedF(Palette.PRIMARY.redF() * (1 - t) + Palette.ACCENT.redF() * t)
            color.setGreenF(Palette.PRIMARY.greenF() * (1 - t) + Palette.ACCENT.greenF() * t)
            color.setBlueF(Palette.PRIMARY.blueF() * (1 - t) + Palette.ACCENT.blueF() * t)
            color.setAlphaF(0.3 + level * 0.6)

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(color))

            # Draw bar mirrored around center
            rect = QRectF(x, center_y - bar_height / 2, bar_width, bar_height)
            painter.drawRoundedRect(rect, bar_width / 2, bar_width / 2)

        painter.end()


# ═══════════════════════════════════════════════════════════════════════════
# Glassmorphism Background Widget
# ═══════════════════════════════════════════════════════════════════════════

class GlassBackground(QWidget):
    """Full-window background with glassmorphism effect and particles."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.particles = ParticleSystem(600, 650, max_particles=50)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(33)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.particles.resize(self.width(), self.height())

    def _tick(self):
        self.particles.update()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        # Dark gradient background
        bg_gradient = QLinearGradient(0, 0, 0, h)
        bg_gradient.setColorAt(0.0, QColor(15, 20, 35, 242))
        bg_gradient.setColorAt(0.5, QColor(17, 24, 39, 245))
        bg_gradient.setColorAt(1.0, QColor(10, 15, 30, 250))
        painter.fillRect(0, 0, w, h, QBrush(bg_gradient))

        # Subtle gradient overlay (top-left indigo glow)
        overlay = QRadialGradient(w * 0.3, h * 0.2, w * 0.6)
        overlay.setColorAt(0.0, QColor(99, 102, 241, 20))
        overlay.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.fillRect(0, 0, w, h, QBrush(overlay))

        # Bottom-right cyan glow
        overlay2 = QRadialGradient(w * 0.7, h * 0.8, w * 0.5)
        overlay2.setColorAt(0.0, QColor(6, 182, 212, 12))
        overlay2.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.fillRect(0, 0, w, h, QBrush(overlay2))

        # Draw particles
        self.particles.draw(painter)

        # Glass card (inner panel)
        self._draw_glass_card(painter, w, h)

        painter.end()

    def _draw_glass_card(self, painter: QPainter, w: float, h: float):
        """Draw the main glassmorphism container card."""
        margin = 15
        card_rect = QRectF(margin, margin, w - 2 * margin, h - 2 * margin)
        radius = 20.0

        path = QPainterPath()
        path.addRoundedRect(card_rect, radius, radius)

        # Semi-transparent fill
        painter.save()
        painter.setClipPath(path)
        fill = QColor(30, 41, 59, 100)
        painter.fillRect(card_rect, fill)
        painter.restore()

        # Subtle border
        border_pen = QPen(QColor(100, 116, 139, 40))
        border_pen.setWidthF(1.0)
        painter.setPen(border_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(card_rect, radius, radius)

        # Top highlight line
        highlight_pen = QPen(QColor(255, 255, 255, 15))
        highlight_pen.setWidthF(1.0)
        painter.setPen(highlight_pen)
        painter.drawLine(
            QPointF(margin + radius, margin),
            QPointF(w - margin - radius, margin),
        )
