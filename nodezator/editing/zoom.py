"""Workspace zoom handling utilities."""

### standard library imports

from math import isclose


### third-party imports

from pygame import Rect

from pygame.math import Vector2

from pygame.mouse import get_pos as get_mouse_pos

from pygame.transform import smoothscale


### local imports

from ..pygamesetup import SCREEN, SCREEN_RECT


### constants

ZOOM_STEP = 0.1
MIN_ZOOM = 0.4
MAX_ZOOM = 2.5


class ZoomHandling:
    """Provide workspace zoom operations."""

    def __init__(self):
        """Initialise zoom controls."""

        self._zoom_factor = 1.0
        self._workspace_rect = Rect(0, 0, *SCREEN_RECT.size)
        self._zoom_view_pos = Vector2()

    # properties ---------------------------------------------------------

    @property
    def workspace_rect(self):
        """Return workspace rect."""

        return self._workspace_rect

    def update_workspace_rect(self, rect):
        """Update workspace rect according to given rect."""

        if rect is None:
            rect = Rect(0, 0, *SCREEN_RECT.size)

        self._workspace_rect = Rect(rect)
        self._constrain_zoom_view()

    @property
    def zoom_factor(self):
        """Return current zoom factor."""

        return self._zoom_factor

    # helpers ------------------------------------------------------------

    def _constrain_zoom_view(self):
        """Ensure zoom view position is within valid bounds."""

        rect = self._workspace_rect

        if not rect.width or not rect.height:
            self._zoom_view_pos.update(0, 0)
            return

        scaled_w = rect.width * self._zoom_factor
        scaled_h = rect.height * self._zoom_factor

        max_x = max(0, scaled_w - rect.width)
        max_y = max(0, scaled_h - rect.height)

        self._zoom_view_pos.x = min(max(self._zoom_view_pos.x, 0), max_x)
        self._zoom_view_pos.y = min(max(self._zoom_view_pos.y, 0), max_y)

    def _relative_anchor(self, screen_pos):
        """Return anchor position relative to workspace."""

        rect = self._workspace_rect

        if not rect.collidepoint(screen_pos):
            return Vector2(rect.center)

        return Vector2(screen_pos) - rect.topleft

    # conversion --------------------------------------------------------

    def workspace_to_screen(self, pos):
        """Convert workspace coordinates to screen coords."""

        rect = self._workspace_rect

        if not rect.width or not rect.height:
            return pos

        scaled_pos = Vector2(pos) * self._zoom_factor
        scaled_pos -= self._zoom_view_pos
        scaled_pos += rect.topleft

        return tuple(int(round(value)) for value in scaled_pos)

    def screen_to_workspace(self, pos):
        """Convert screen coordinates to workspace ones."""

        rect = self._workspace_rect

        if not rect.width or not rect.height:
            return pos

        relative = Vector2(pos) - rect.topleft

        relative += self._zoom_view_pos

        if self._zoom_factor:
            relative /= self._zoom_factor

        return tuple(relative)

    def get_workspace_mouse_pos(self):
        """Return current mouse position in workspace coordinates."""

        return self.screen_to_workspace(get_mouse_pos())

    # zoom changing -----------------------------------------------------

    def change_zoom(self, steps, anchor_screen_pos):
        """Adjust zoom factor based on wheel steps."""

        if not steps:
            return

        old_zoom = self._zoom_factor

        new_zoom = round(old_zoom + steps * ZOOM_STEP, 2)
        new_zoom = max(MIN_ZOOM, min(MAX_ZOOM, new_zoom))

        if isclose(new_zoom, old_zoom, rel_tol=1e-3):
            return

        anchor = self._relative_anchor(anchor_screen_pos)

        world_pos = (self._zoom_view_pos + anchor) / old_zoom

        self._zoom_factor = new_zoom

        self._zoom_view_pos = world_pos * new_zoom - anchor

        self._constrain_zoom_view()

    # drawing -----------------------------------------------------------

    def draw_zoomed_workspace(self):
        """Apply zooming to workspace area."""

        rect = self._workspace_rect

        if not rect.width or not rect.height:
            return

        zoom = self._zoom_factor

        if isclose(zoom, 1.0, rel_tol=1e-3) and self._zoom_view_pos.length_squared() < 1:
            return

        area = SCREEN.subsurface(rect).copy()

        scaled_size = (
            max(1, int(round(rect.width * zoom))),
            max(1, int(round(rect.height * zoom))),
        )

        scaled = smoothscale(area, scaled_size)

        result = area.copy()
        fill_color = area.get_at((0, 0))
        result.fill(fill_color)

        scaled_rect = Rect((0, 0), scaled_size)

        if scaled_rect.width <= rect.width:
            view_width = scaled_rect.width
            src_x = 0
            dest_x = (rect.width - view_width) // 2
        else:
            view_width = rect.width
            max_x = scaled_rect.width - view_width
            src_x = min(max(int(round(self._zoom_view_pos.x)), 0), max_x)
            dest_x = 0

        if scaled_rect.height <= rect.height:
            view_height = scaled_rect.height
            src_y = 0
            dest_y = (rect.height - view_height) // 2
        else:
            view_height = rect.height
            max_y = scaled_rect.height - view_height
            src_y = min(max(int(round(self._zoom_view_pos.y)), 0), max_y)
            dest_y = 0

        view_rect = Rect(src_x, src_y, view_width, view_height)

        cropped = scaled.subsurface(view_rect)

        result.blit(cropped, (dest_x, dest_y))

        SCREEN.blit(result, rect.topleft)

