"""Workspace zoom handling utilities with world sampling support."""

### standard library imports

from math import isclose, floor


### third-party imports

from pygame import Rect, Surface
from pygame.math import Vector2
from pygame.mouse import get_pos as get_mouse_pos
from pygame.transform import smoothscale
from pygame.draw import line as draw_line, rect as draw_rect


### local imports

from ..config import APP_REFS

from ..pygamesetup import SCREEN, SCREEN_RECT

from ..colorsman.colors import (
    GRAPH_BG,
    SMALL_GRID_COLOR,
    ACTIVE_SELECTION,
    NORMAL_SELECTION,
)


### constants

ZOOM_STEP_FACTOR = 1.2
MIN_ZOOM = 0.2
MAX_ZOOM = 4.0
WORLD_MARGIN = 200
GRID_SPACING = 80


class ZoomHandling:
    """Provide workspace zoom operations for the editing canvas."""

    def __init__(self):
        """Initialise zoom controls and world sampling data."""

        self._zoom_scale = 1.0
        self._workspace_rect = Rect(0, 0, *SCREEN_RECT.size)
        self._view_topleft = Vector2()

        self._world_surface = None
        self._world_rect = Rect(0, 0, 0, 0)

    # basic data ---------------------------------------------------------

    @property
    def workspace_rect(self):
        """Return workspace rect."""

        return self._workspace_rect

    def update_workspace_rect(self, rect):
        """Update workspace rect according to given rect."""

        if rect is None:
            rect = Rect(0, 0, *SCREEN_RECT.size)

        self._workspace_rect = Rect(rect)
        self._clamp_view()

    @property
    def zoom_factor(self):
        """Return current zoom factor."""

        return self._zoom_scale

    # coordinate helpers ------------------------------------------------

    def _relative_anchor(self, screen_pos):
        """Return anchor position relative to workspace."""

        rect = self._workspace_rect

        if not rect.collidepoint(screen_pos):
            return Vector2(rect.center)

        return Vector2(screen_pos) - rect.topleft

    def workspace_to_screen(self, pos):
        """Convert workspace/world coordinates to screen coords."""

        rect = self._workspace_rect
        if not rect.width or not rect.height:
            return pos

        relative = Vector2(pos) - self._view_topleft
        scaled = relative * self._zoom_scale
        scaled += rect.topleft
        return tuple(int(round(value)) for value in scaled)

    def screen_to_workspace(self, pos):
        """Convert screen coordinates to workspace ones."""

        rect = self._workspace_rect
        if not rect.width or not rect.height:
            return pos

        relative = Vector2(pos) - rect.topleft
        if self._zoom_scale:
            relative /= self._zoom_scale
        relative += self._view_topleft
        return tuple(relative)

    def get_workspace_mouse_pos(self):
        """Return current mouse position in workspace coordinates."""

        return self.screen_to_workspace(get_mouse_pos())

    # world generation ---------------------------------------------------

    def _ensure_world_surface(self):
        """Ensure world surface is up to date with the graph."""

        gm = APP_REFS.gm

        try:
            union_rect = gm.rectsman.union_rect
        except RuntimeError:
            self._world_surface = None
            self._world_rect = Rect(0, 0, 0, 0)
            return

        union_rect = Rect(union_rect)
        if not union_rect.width or not union_rect.height:
            self._world_surface = None
            self._world_rect = Rect(0, 0, 0, 0)
            return

        world_rect = union_rect.inflate(WORLD_MARGIN * 2, WORLD_MARGIN * 2)
        world_rect.union_ip(self._workspace_rect)

        size = world_rect.size
        world_surface = Surface(size).convert(SCREEN)
        world_surface.fill(GRAPH_BG)

        delta = Vector2(-world_rect.left, -world_rect.top)
        gm.rectsman.move_ip(delta)

        try:
            self._draw_world_grid(world_surface, world_rect)
            self._draw_world_objects(world_surface)
            self._draw_world_lines(world_surface)
            self._draw_world_selection(world_surface)
        finally:
            gm.rectsman.move_ip(-delta)

        self._world_surface = world_surface
        self._world_rect = world_rect
        self._clamp_view()

    def _draw_world_grid(self, surf, world_rect):
        """Draw scrolling grid representation onto surface."""

        ea = APP_REFS.ea
        width, height = surf.get_size()

        offset_x = ea.scrolling_amount.x
        offset_y = ea.scrolling_amount.y

        start_index_x = floor((world_rect.left - offset_x) / GRID_SPACING)
        x = start_index_x * GRID_SPACING + offset_x

        while x <= world_rect.right:
            surf_x = x - world_rect.left
            draw_line(surf, SMALL_GRID_COLOR, (surf_x, 0), (surf_x, height), 1)
            x += GRID_SPACING

        start_index_y = floor((world_rect.top - offset_y) / GRID_SPACING)
        y = start_index_y * GRID_SPACING + offset_y

        while y <= world_rect.bottom:
            surf_y = y - world_rect.top
            draw_line(surf, SMALL_GRID_COLOR, (0, surf_y), (width, surf_y), 1)
            y += GRID_SPACING

    def _draw_world_objects(self, surf):
        """Draw nodes, previews and text blocks onto the world surface."""

        gm = APP_REFS.gm
        blit = surf.blit

        for obj in gm.preview_panels:
            blit(obj.image, obj.rect)

        for obj in gm.preview_toolbars:
            blit(obj.image, obj.rect)

        for node in gm.nodes:
            node.draw_on_surf(surf)

        gm.text_blocks.draw_on_surf(surf)

    def _draw_world_lines(self, surf):
        """Draw connections on the world surface."""

        gm = APP_REFS.gm
        for parent in gm.parents:
            parent_center = parent.rect.center
            color = parent.line_color
            for child in parent.children:
                draw_line(surf, color, parent_center, child.rect.center, 4)

    def _draw_world_selection(self, surf):
        """Draw selection outlines on the world surface."""

        ea = APP_REFS.ea

        for obj in ea.selected_objs:
            color = ACTIVE_SELECTION if obj is ea.active_obj else NORMAL_SELECTION

            if hasattr(obj, "rectsman"):
                rect = obj.rect.inflate(-8, 4)
            else:
                rect = obj.rect.inflate(4, 4)

            draw_rect(surf, color, rect, 4)

    # clamping -----------------------------------------------------------

    def _clamp_view(self):
        """Ensure the view window stays within world bounds."""

        rect = self._workspace_rect
        world = self._world_rect

        if not rect.width or not rect.height or not world.width or not world.height:
            self._view_topleft.update(0, 0)
            return

        view_w = rect.width / self._zoom_scale
        view_h = rect.height / self._zoom_scale

        min_x = world.left
        min_y = world.top
        max_x = world.right - view_w
        max_y = world.bottom - view_h

        if view_w >= world.width:
            min_x = max_x = world.left - (view_w - world.width) / 2

        if view_h >= world.height:
            min_y = max_y = world.top - (view_h - world.height) / 2

        self._view_topleft.x = max(min(self._view_topleft.x, max_x), min_x)
        self._view_topleft.y = max(min(self._view_topleft.y, max_y), min_y)

    # zoom changing ------------------------------------------------------

    def change_zoom(self, steps, anchor_screen_pos):
        """Adjust zoom scale based on wheel steps."""

        if not steps:
            return

        old_scale = self._zoom_scale

        if steps > 0:
            new_scale = old_scale * (ZOOM_STEP_FACTOR ** steps)
        else:
            new_scale = old_scale / (ZOOM_STEP_FACTOR ** (-steps))

        new_scale = max(MIN_ZOOM, min(MAX_ZOOM, new_scale))

        if isclose(new_scale, old_scale, rel_tol=1e-4):
            return

        anchor = self._relative_anchor(anchor_screen_pos)
        world_anchor = self._view_topleft + (anchor / old_scale)

        self._zoom_scale = new_scale
        self._view_topleft = world_anchor - (anchor / new_scale)

        self._clamp_view()

    # drawing ------------------------------------------------------------

    def draw_zoomed_workspace(self):
        """Apply zooming to workspace area by sampling the world surface."""

        rect = self._workspace_rect
        if not rect.width or not rect.height:
            return

        self._ensure_world_surface()

        if self._world_surface is None:
            return

        if isclose(self._zoom_scale, 1.0, rel_tol=1e-4) and self._view_topleft.length_squared() < 1:
            return

        view_w = max(1, int(round(rect.width / self._zoom_scale)))
        view_h = max(1, int(round(rect.height / self._zoom_scale)))

        source_left = int(round(self._view_topleft.x - self._world_rect.left))
        source_top = int(round(self._view_topleft.y - self._world_rect.top))

        source_rect = Rect(source_left, source_top, view_w, view_h)
        world_rect = self._world_surface.get_rect()
        intersection = source_rect.clip(world_rect)

        view_surface = Surface((view_w, view_h)).convert(self._world_surface)
        view_surface.fill(GRAPH_BG)

        if intersection.width and intersection.height:
            dest = (
                intersection.left - source_rect.left,
                intersection.top - source_rect.top,
            )
            view_surface.blit(self._world_surface, dest, intersection)

        scaled = smoothscale(view_surface, rect.size)
        SCREEN.blit(scaled, rect.topleft)
