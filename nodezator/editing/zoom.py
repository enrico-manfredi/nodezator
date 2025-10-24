"""Workspace zoom handling utilities."""

### standard library imports

from math import isclose


### third-party imports

from pygame import Rect, Surface

from pygame.math import Vector2

from pygame.mouse import get_pos as get_mouse_pos

from pygame.transform import smoothscale


### local imports

from ..config import APP_REFS

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
        self._world_rect = Rect(self._workspace_rect)
        self._world_surface = None
        self._world_surface_rect = Rect(0, 0, 0, 0)
        self._world_offset = Vector2()
        self._world_scale = 1.0
        self._world_background = None
        self._world_has_content = False

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
        self._compute_world_rect()
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

        zoom = self._zoom_factor or 1.0
        world_rect = self._world_rect

        view_width = rect.width / zoom
        view_height = rect.height / zoom

        world_view_x = self._zoom_view_pos.x / zoom
        world_view_y = self._zoom_view_pos.y / zoom

        min_x = world_rect.left
        min_y = world_rect.top
        max_x = world_rect.right - view_width
        max_y = world_rect.bottom - view_height

        if world_rect.width <= 0 or view_width >= world_rect.width:
            world_view_x = world_rect.left - (view_width - world_rect.width) / 2
        else:
            world_view_x = min(max(world_view_x, min_x), max_x)

        if world_rect.height <= 0 or view_height >= world_rect.height:
            world_view_y = world_rect.top - (view_height - world_rect.height) / 2
        else:
            world_view_y = min(max(world_view_y, min_y), max_y)

        self._zoom_view_pos.x = world_view_x * zoom
        self._zoom_view_pos.y = world_view_y * zoom

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

        self._compute_world_rect()

        old_zoom = self._zoom_factor

        base = 1.0 + ZOOM_STEP
        new_zoom = old_zoom * (base ** steps)

        rect = self._workspace_rect
        world = self._world_rect

        min_zoom = MIN_ZOOM

        if world.width and world.height:
            width_ratio = rect.width / world.width if world.width else MIN_ZOOM
            height_ratio = rect.height / world.height if world.height else MIN_ZOOM
            min_zoom = min(min_zoom, width_ratio, height_ratio)

        new_zoom = max(min_zoom, min(MAX_ZOOM, new_zoom))

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
        self._update_world_surface()

        if self._world_surface is None:
            return

        view_width = max(1, int(round(rect.width / zoom)))
        view_height = max(1, int(round(rect.height / zoom)))

        world_view_x = (self._zoom_view_pos.x / zoom)
        world_view_y = (self._zoom_view_pos.y / zoom)

        view_surface = Surface((view_width, view_height)).convert(self._world_surface)
        view_surface.fill(self._world_background)

        src_rect = Rect(
            int(round(world_view_x - self._world_rect.left)),
            int(round(world_view_y - self._world_rect.top)),
            view_width,
            view_height,
        )

        clipped = src_rect.clip(self._world_surface_rect)

        if clipped.width and clipped.height:
            dest = (
                clipped.left - src_rect.left,
                clipped.top - src_rect.top,
            )
            view_surface.blit(self._world_surface, dest, clipped)

        if view_surface.get_size() == rect.size:
            SCREEN.blit(view_surface, rect.topleft)
        else:
            scaled = smoothscale(view_surface, rect.size)
            SCREEN.blit(scaled, rect.topleft)

    # world surface management -----------------------------------------

    def _compute_world_rect(self):
        """Refresh world rect/offset from graph data."""

        rect = self._workspace_rect

        if not rect.width or not rect.height:
            self._world_rect = Rect(rect)
            self._world_offset.update(0, 0)
            self._world_has_content = False
            return

        gm = getattr(APP_REFS, "gm", None)

        has_objects = False
        union_rect = None

        if gm is not None:
            has_objects = any(
                (
                    gm.nodes,
                    gm.text_blocks,
                    gm.preview_panels,
                    gm.preview_toolbars,
                )
            )

            if has_objects:
                try:
                    union_rect = gm.rectsman.union_rect.copy()
                except RuntimeError:
                    has_objects = False

        if not has_objects or union_rect is None:
            union_rect = Rect(rect)

        if not union_rect.width:
            union_rect.width = max(1, rect.width)

        if not union_rect.height:
            union_rect.height = max(1, rect.height)

        self._world_rect = union_rect
        self._world_offset.update(-union_rect.left, -union_rect.top)
        self._world_has_content = has_objects

    def _update_world_surface(self):
        """Build world surface reflecting current graph state."""

        self._compute_world_rect()

        world_rect = self._world_rect
        rect = self._workspace_rect

        width = max(1, world_rect.width)
        height = max(1, world_rect.height)

        background = SCREEN.get_at(rect.topleft)

        world_surface = Surface((width, height)).convert(SCREEN)
        world_surface.fill(background)

        gm = getattr(APP_REFS, "gm", None)

        if gm is not None and self._world_has_content:
            dx = -world_rect.left
            dy = -world_rect.top
            moved = False

            if dx or dy:
                try:
                    gm.rectsman.move_ip(dx, dy)
                except RuntimeError:
                    pass
                else:
                    moved = True

            try:
                for panel in gm.preview_panels:
                    panel.draw_on_surf(world_surface)

                for toolbar in gm.preview_toolbars:
                    toolbar.draw_on_surf(world_surface)

                gm.draw_lines_on_surf(world_surface)

                for node in gm.nodes:
                    node.draw_on_surf(world_surface)

                gm.text_blocks.draw_on_surf(world_surface)

            finally:
                if moved:
                    gm.rectsman.move_ip(-dx, -dy)

        self._world_surface = world_surface
        self._world_surface_rect = world_surface.get_rect()
        self._world_background = background
        self._world_scale = 1.0
        self._constrain_zoom_view()

