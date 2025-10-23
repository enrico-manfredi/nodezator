"""Helpers for applying zoom effects to the main screen."""

from __future__ import annotations

from dataclasses import dataclass, field

from pygame import Surface
from pygame.math import Vector2
from pygame.transform import smoothscale


@dataclass
class ZoomState:
    """Container for zoom values."""

    scale: float = 1.0
    offset: Vector2 = field(default_factory=Vector2)


class ZoomManager:
    """Maintain state and helpers for zooming the screen."""

    def __init__(self, screen_size):
        self._screen_size = Vector2(screen_size)
        self.state = ZoomState()
        self.min_scale = 0.25
        self.max_scale = 4.0

    # ------------------------------------------------------------------
    # basic data handling
    # ------------------------------------------------------------------
    @property
    def scale(self) -> float:
        return self.state.scale

    @property
    def offset(self) -> Vector2:
        return self.state.offset

    def set_screen_size(self, size):
        """Store the screen size for future calculations."""

        self._screen_size.xy = size

    # ------------------------------------------------------------------
    # coordinate conversions
    # ------------------------------------------------------------------
    def screen_to_world(self, point):
        """Convert a screen point to the unscaled coordinate space."""

        if self.state.scale == 1.0:
            return point

        return (Vector2(point) + self.state.offset) / self.state.scale

    def world_to_screen(self, point):
        """Convert a world point to screen coordinates."""

        if self.state.scale == 1.0:
            return point

        return Vector2(point) * self.state.scale - self.state.offset

    # ------------------------------------------------------------------
    # zoom manipulation
    # ------------------------------------------------------------------
    def change_zoom(self, direction: int, anchor_point):
        """Change zoom using mouse wheel direction and anchor point.

        Parameters
        ----------
        direction:
            Positive integers zoom in, negative integers zoom out.
        anchor_point:
            Point in *world* coordinates where the zoom should pivot.
        """

        if direction == 0:
            return

        step = 0.1
        new_scale = self.state.scale * (1 + step) ** direction
        new_scale = max(self.min_scale, min(self.max_scale, new_scale))

        if new_scale == self.state.scale:
            return

        if new_scale == 1.0:
            self.state.scale = 1.0
            self.state.offset.update((0, 0))
            return

        anchor_screen = Vector2(self.world_to_screen(anchor_point))
        world_anchor = Vector2(anchor_point)
        self.state.scale = new_scale
        self.state.offset = (world_anchor * new_scale) - anchor_screen

    def reset(self):
        """Reset zoom to default."""

        self.state.scale = 1.0
        self.state.offset.update((0, 0))

    # ------------------------------------------------------------------
    # rendering helpers
    # ------------------------------------------------------------------
    def apply(self, screen: Surface):
        """Apply the zoom effect on the provided screen surface."""

        scale = self.state.scale

        if scale == 1.0:
            return

        base = screen.copy()
        scaled_size = [max(1, round(value * scale)) for value in base.get_size()]
        scaled = smoothscale(base, scaled_size)

        offset = self.state.offset
        screen.fill(base.get_at((0, 0)))
        screen.blit(scaled, (-offset.x, -offset.y))


# alias used elsewhere
__all__ = ["ZoomManager"]

