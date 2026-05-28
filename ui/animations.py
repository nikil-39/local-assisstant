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
            self._ring_rotation += 1.5
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

        # Draw energy field (outermost layer — subtle pulsing halo)
        self._draw_energy_field(painter, cx, cy, r)

        # Draw concentric rings
        self._draw_rings(painter, cx, cy, r)

        # Draw orbiting data nodes
        self._draw_orbit_nodes(painter, cx, cy, r)

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
            self._draw_electric_arcs(painter, cx, cy, r)
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

    def _draw_energy_field(self, painter: QPainter, cx: float, cy: float, r: float):
        """Draw a pulsing energy field / halo around the orb."""
        painter.save()
        # Multiple concentric pulsing halos at different phases
        for i in range(3):
            phase = self._pulse_phase + i * (2 * math.pi / 3)
            pulse = 0.3 + 0.7 * abs(math.sin(phase * 0.5))
            halo_r = r * (1.6 + i * 0.15) * self._scale
            alpha = int(8 * pulse)

            color = QColor(Palette.ACCENT) if i % 2 == 0 else QColor(Palette.SECONDARY)
            color.setAlpha(alpha)
            pen = QPen(color)
            pen.setWidthF(1.0 + pulse)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(QPointF(cx, cy), halo_r, halo_r)
        painter.restore()

    def _draw_orbit_nodes(self, painter: QPainter, cx: float, cy: float, r: float):
        """Draw small glowing data nodes orbiting the orb."""
        painter.save()
        node_count = 6
        orbit_r = r * 1.35 * self._scale

        for i in range(node_count):
            # Each node orbits at different speed/direction
            angle = math.radians(self._ring_rotation * (1.2 if i % 2 == 0 else -0.8) + i * (360 / node_count))
            # Slight vertical wobble
            wobble = math.sin(self._pulse_phase + i) * 5
            nx = cx + math.cos(angle) * orbit_r
            ny = cy + math.sin(angle) * orbit_r + wobble

            # Node glow
            node_size = 3.0 + 1.5 * abs(math.sin(self._pulse_phase + i * 1.2))
            glow_grad = QRadialGradient(nx, ny, node_size * 3)
            glow_color = QColor(Palette.ACCENT) if i % 2 == 0 else QColor(Palette.PRIMARY)
            glow_color.setAlpha(60)
            glow_grad.setColorAt(0.0, glow_color)
            glow_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(glow_grad))
            painter.drawEllipse(QPointF(nx, ny), node_size * 3, node_size * 3)

            # Node core
            core_color = QColor(220, 240, 255, 200)
            painter.setBrush(QBrush(core_color))
            painter.drawEllipse(QPointF(nx, ny), node_size, node_size)

            # Trail line connecting to orb center (faint)
            trail_color = QColor(Palette.ACCENT)
            trail_color.setAlpha(15)
            pen = QPen(trail_color)
            pen.setWidthF(0.5)
            painter.setPen(pen)
            painter.drawLine(QPointF(cx, cy), QPointF(nx, ny))

        painter.restore()

    def _draw_electric_arcs(self, painter: QPainter, cx: float, cy: float, r: float):
        """Draw crackling electric arcs during processing (randomized each frame)."""
        painter.save()
        orb_r = r * self._scale
        arc_count = 3

        for _ in range(arc_count):
            # Random start angle on the orb edge
            start_angle = random.uniform(0, 2 * math.pi)
            sx = cx + math.cos(start_angle) * orb_r
            sy = cy + math.sin(start_angle) * orb_r

            # End point further out
            end_dist = orb_r + random.uniform(15, 40)
            end_angle = start_angle + random.uniform(-0.4, 0.4)
            ex = cx + math.cos(end_angle) * end_dist
            ey = cy + math.sin(end_angle) * end_dist

            # Draw jagged line (2-3 segments)
            path = QPainterPath()
            path.moveTo(sx, sy)
            segments = random.randint(2, 4)
            for s in range(1, segments):
                t = s / segments
                mx = sx + (ex - sx) * t + random.uniform(-8, 8)
                my = sy + (ey - sy) * t + random.uniform(-8, 8)
                path.lineTo(mx, my)
            path.lineTo(ex, ey)

            color = QColor(120, 200, 255, random.randint(100, 200))
            pen = QPen(color)
            pen.setWidthF(random.uniform(1.0, 2.0))
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(path)

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
    """Full-window background with holographic glassmorphism effect and particles."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.particles = ParticleSystem(600, 650, max_particles=50)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(33)
        self._frame = 0  # frame counter for animated effects
        # Data rain columns (matrix-style falling characters)
        self._rain_columns: list[dict] = []
        self._init_rain(600)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.particles.resize(self.width(), self.height())
        self._init_rain(self.width())

    def _init_rain(self, width: int):
        """Initialize data rain columns across the width."""
        col_spacing = 25
        self._rain_columns = []
        for x in range(0, width, col_spacing):
            self._rain_columns.append({
                "x": x,
                "y": random.uniform(-200, 0),
                "speed": random.uniform(1.5, 4.0),
                "chars": [chr(random.randint(0x30A0, 0x30FF)) for _ in range(random.randint(5, 15))],
                "alpha_base": random.uniform(0.03, 0.08),
            })

    def _tick(self):
        self._frame += 1
        self.particles.update()
        # Update rain
        for col in self._rain_columns:
            col["y"] += col["speed"]
            if col["y"] > self.height() + 200:
                col["y"] = random.uniform(-300, -50)
                col["speed"] = random.uniform(1.5, 4.0)
                col["chars"] = [chr(random.randint(0x30A0, 0x30FF)) for _ in range(random.randint(5, 15))]
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        # Dark gradient background
        bg_gradient = QLinearGradient(0, 0, 0, h)
        bg_gradient.setColorAt(0.0, QColor(8, 12, 24, 250))
        bg_gradient.setColorAt(0.5, QColor(12, 18, 32, 252))
        bg_gradient.setColorAt(1.0, QColor(6, 10, 20, 255))
        painter.fillRect(0, 0, w, h, QBrush(bg_gradient))

        # Holographic shimmer overlay (animated diagonal sweep)
        self._draw_hologram_shimmer(painter, w, h)

        # Subtle gradient overlay (top-left indigo glow)
        overlay = QRadialGradient(w * 0.3, h * 0.2, w * 0.6)
        overlay.setColorAt(0.0, QColor(99, 102, 241, 25))
        overlay.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.fillRect(0, 0, w, h, QBrush(overlay))

        # Bottom-right cyan glow
        overlay2 = QRadialGradient(w * 0.7, h * 0.8, w * 0.5)
        overlay2.setColorAt(0.0, QColor(6, 182, 212, 15))
        overlay2.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.fillRect(0, 0, w, h, QBrush(overlay2))

        # Hex grid pattern (hologram texture)
        self._draw_hex_grid(painter, w, h)

        # Draw particles
        self.particles.draw(painter)

        # Data rain (faint matrix-style falling characters)
        self._draw_data_rain(painter, w, h)

        # Circuit traces (animated light pulses along paths)
        self._draw_circuit_traces(painter, w, h)

        # Glass card (inner panel)
        self._draw_glass_card(painter, w, h)

        # Scanline overlay (CRT/hologram feel)
        self._draw_scanlines(painter, w, h)

        # Edge glow (flickering border)
        self._draw_edge_glow(painter, w, h)

        painter.end()

    def _draw_hologram_shimmer(self, painter: QPainter, w: float, h: float):
        """Animated diagonal light sweep like a holographic card."""
        painter.save()
        # Sweep position oscillates across the window
        sweep_x = (self._frame * 2) % (w + 200) - 100
        shimmer_grad = QLinearGradient(sweep_x - 60, 0, sweep_x + 60, h)
        shimmer_grad.setColorAt(0.0, QColor(0, 0, 0, 0))
        shimmer_grad.setColorAt(0.4, QColor(99, 220, 255, 8))
        shimmer_grad.setColorAt(0.5, QColor(180, 140, 255, 12))
        shimmer_grad.setColorAt(0.6, QColor(99, 220, 255, 8))
        shimmer_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.fillRect(0, 0, int(w), int(h), QBrush(shimmer_grad))
        painter.restore()

    def _draw_hex_grid(self, painter: QPainter, w: float, h: float):
        """Draw a subtle hexagonal grid pattern."""
        painter.save()
        hex_size = 30
        color = QColor(99, 102, 241, 8)
        pen = QPen(color)
        pen.setWidthF(0.5)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        row_h = hex_size * 1.732
        for row in range(int(h / row_h) + 2):
            for col in range(int(w / (hex_size * 3)) + 2):
                cx = col * hex_size * 3 + (hex_size * 1.5 if row % 2 else 0)
                cy = row * row_h * 0.5
                path = QPainterPath()
                for i in range(6):
                    angle = math.radians(60 * i - 30)
                    px = cx + hex_size * 0.5 * math.cos(angle)
                    py = cy + hex_size * 0.5 * math.sin(angle)
                    if i == 0:
                        path.moveTo(px, py)
                    else:
                        path.lineTo(px, py)
                path.closeSubpath()
                painter.drawPath(path)
        painter.restore()

    def _draw_scanlines(self, painter: QPainter, w: float, h: float):
        """Subtle horizontal scanlines for holographic CRT feel."""
        painter.save()
        # Only draw every 3rd pixel row for performance
        color = QColor(0, 0, 0, 12)
        pen = QPen(color)
        pen.setWidthF(1.0)
        painter.setPen(pen)
        for y in range(0, int(h), 3):
            painter.drawLine(0, y, int(w), y)
        painter.restore()

    def _draw_edge_glow(self, painter: QPainter, w: float, h: float):
        """Animated flickering glow along the window edges."""
        painter.save()
        # Flicker intensity based on frame
        flicker = 0.5 + 0.5 * math.sin(self._frame * 0.1)
        alpha = int(20 + 15 * flicker)

        margin = 15
        rect = QRectF(margin, margin, w - 2 * margin, h - 2 * margin)
        radius = 20.0

        # Cyan edge glow
        glow_pen = QPen(QColor(6, 182, 212, alpha))
        glow_pen.setWidthF(1.5)
        painter.setPen(glow_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(rect, radius, radius)

        # Inner subtle indigo glow
        inner_rect = QRectF(margin + 2, margin + 2, w - 2 * margin - 4, h - 2 * margin - 4)
        glow_pen2 = QPen(QColor(99, 102, 241, int(alpha * 0.5)))
        glow_pen2.setWidthF(0.8)
        painter.setPen(glow_pen2)
        painter.drawRoundedRect(inner_rect, radius - 1, radius - 1)
        painter.restore()

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

    def _draw_data_rain(self, painter: QPainter, w: float, h: float):
        """Draw faint matrix-style falling characters in the background."""
        painter.save()
        font = QFont("Consolas", 9)
        painter.setFont(font)

        for col in self._rain_columns:
            x = col["x"]
            base_y = col["y"]
            chars = col["chars"]
            alpha_base = col["alpha_base"]

            for i, ch in enumerate(chars):
                cy = base_y + i * 14
                if cy < -14 or cy > h + 14:
                    continue
                # Head character is brightest, tail fades
                fade = 1.0 - (i / len(chars))
                alpha = alpha_base * fade
                if i == 0:
                    # Leading character glows brighter (cyan)
                    color = QColor(100, 240, 255, int(alpha * 255 * 3))
                else:
                    color = QColor(99, 102, 241, int(alpha * 255))
                painter.setPen(color)
                painter.drawText(QPointF(x, cy), ch)

        painter.restore()

    def _draw_circuit_traces(self, painter: QPainter, w: float, h: float):
        """Draw animated circuit-board traces with light pulses travelling along them."""
        painter.save()
        # Define a few static circuit paths (relative to window size)
        traces = [
            # (start_x_frac, start_y_frac, segments as list of (dx_frac, dy_frac))
            (0.05, 0.3, [(0.1, 0), (0, 0.08), (0.08, 0), (0, -0.05)]),
            (0.85, 0.2, [(-0.08, 0), (0, 0.1), (-0.06, 0), (0, 0.06)]),
            (0.1, 0.75, [(0.12, 0), (0, -0.06), (0.05, 0), (0, 0.08), (0.07, 0)]),
            (0.75, 0.85, [(-0.1, 0), (0, -0.08), (-0.05, 0)]),
            (0.5, 0.05, [(0.08, 0), (0, 0.06), (0.06, 0), (0, 0.04)]),
        ]

        for idx, (sx_f, sy_f, segs) in enumerate(traces):
            # Build absolute path points
            points = [(sx_f * w, sy_f * h)]
            for dx_f, dy_f in segs:
                prev = points[-1]
                points.append((prev[0] + dx_f * w, prev[1] + dy_f * h))

            # Draw static trace line (very faint)
            trace_color = QColor(99, 102, 241, 12)
            pen = QPen(trace_color)
            pen.setWidthF(1.0)
            painter.setPen(pen)
            for i in range(len(points) - 1):
                painter.drawLine(QPointF(*points[i]), QPointF(*points[i + 1]))

            # Draw node dots at corners
            node_color = QColor(6, 182, 212, 20)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(node_color))
            for pt in points:
                painter.drawEllipse(QPointF(*pt), 2, 2)

            # Animated pulse travelling along the trace
            # Each trace has its own phase offset
            total_length = sum(
                math.hypot(points[i+1][0] - points[i][0], points[i+1][1] - points[i][1])
                for i in range(len(points) - 1)
            )
            if total_length == 0:
                continue

            # Pulse position cycles along total length
            speed = 2.0 + idx * 0.3
            pulse_pos = (self._frame * speed + idx * 80) % total_length

            # Find which segment the pulse is on
            accumulated = 0.0
            px, py = points[0]
            for i in range(len(points) - 1):
                seg_len = math.hypot(points[i+1][0] - points[i][0], points[i+1][1] - points[i][1])
                if accumulated + seg_len >= pulse_pos:
                    t = (pulse_pos - accumulated) / seg_len if seg_len > 0 else 0
                    px = points[i][0] + (points[i+1][0] - points[i][0]) * t
                    py = points[i][1] + (points[i+1][1] - points[i][1]) * t
                    break
                accumulated += seg_len

            # Draw pulse glow
            pulse_grad = QRadialGradient(px, py, 12)
            pulse_grad.setColorAt(0.0, QColor(6, 220, 255, 80))
            pulse_grad.setColorAt(0.5, QColor(99, 102, 241, 30))
            pulse_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(pulse_grad))
            painter.drawEllipse(QPointF(px, py), 12, 12)

            # Bright core
            painter.setBrush(QBrush(QColor(200, 240, 255, 150)))
            painter.drawEllipse(QPointF(px, py), 2.5, 2.5)

        painter.restore()
