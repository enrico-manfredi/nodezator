"""Viewer for the graph history timeline."""

### standard library imports

from functools import partial


### third-party imports

from pygame.draw import circle as draw_circle, line as draw_line

from pygame.locals import (
    QUIT,
    KEYUP,
    KEYDOWN,
    K_ESCAPE,
    K_UP,
    K_DOWN,
    MOUSEBUTTONDOWN,
    MOUSEWHEEL,
)


### local imports

from ..pygamesetup import SERVICES_NS, SCREEN_RECT, blit_on_screen

from ..surfsman.cache import UNHIGHLIGHT_SURF_MAP

from ..surfsman.draw import draw_border

from ..surfsman.render import render_rect

from ..textman.render import render_text

from ..classes2d.single import Object2D

from ..colorsman.colors import (
    BUTTON_BG,
    BUTTON_FG,
    CONTRAST_LAYER_COLOR,
    HOVERED_BUTTON_BG,
    WINDOW_BG,
    WINDOW_FG,
)

from ..fontsman.constants import ENC_SANS_BOLD_FONT_HEIGHT

from ..loopman.exception import QuitAppException, SwitchLoopException


HEADER_SETTINGS = {
    "font_height": ENC_SANS_BOLD_FONT_HEIGHT,
    "foreground_color": WINDOW_FG,
    "background_color": (*WINDOW_BG, 0),
    "padding": 4,
}


TEXT_SETTINGS = {
    "font_height": ENC_SANS_BOLD_FONT_HEIGHT,
    "foreground_color": WINDOW_FG,
    "background_color": (*WINDOW_BG, 0),
    "padding": 2,
}


class HistoryViewer(Object2D):
    """Display history entries as a linked timeline."""

    node_radius = 16
    node_spacing = 90

    def __init__(self, history):
        """Build viewer for given history."""

        self.history = history

        width = 560
        height = min(480, max(240, self._estimate_height()))

        image = render_rect(width, height, WINDOW_BG)
        draw_border(image)

        super().__init__(image=image, rect=image.get_rect())

        self.rect.center = SCREEN_RECT.center

        self.rect_size_semitransp_obj = Object2D.from_surface(
            surface=render_rect(
                *SCREEN_RECT.size,
                (*CONTRAST_LAYER_COLOR, 130),
            ),
            coordinates_name="topleft",
            coordinates_value=(0, 0),
        )

        self.content_surface = None
        self.node_hitboxes = []
        self.scroll_offset = 0
        self.max_scroll = 0

        self.leave = partial(setattr, self, "running", False)

        self._render_timeline()

    # --- presentation --------------------------------------------------

    def present(self):
        """Present the viewer in a modal fashion."""

        blit_on_screen(UNHIGHLIGHT_SURF_MAP[SCREEN_RECT.size], (0, 0))

        self.running = True
        self.loop_holder = self

        while True:
            try:
                while self.running:
                    SERVICES_NS.frame_checkups()
                    self.loop_holder.handle_input()
                    self.loop_holder.update()
                    self.loop_holder.draw()

                break

            except SwitchLoopException as err:
                self.loop_holder = err.loop_holder

        self.rect_size_semitransp_obj.draw()

    def handle_input(self):
        """Process input events."""

        for event in SERVICES_NS.get_events():

            if event.type == QUIT:
                raise QuitAppException

            elif event.type == KEYUP:
                if event.key == K_ESCAPE:
                    self.leave()

            elif event.type == KEYDOWN:
                if event.key == K_UP:
                    self.scroll_offset = max(self.scroll_offset - 40, 0)
                elif event.key == K_DOWN:
                    self.scroll_offset = min(self.scroll_offset + 40, self.max_scroll)

            elif event.type == MOUSEWHEEL:
                self.scroll_offset = min(
                    max(self.scroll_offset - (event.y * 40), 0),
                    self.max_scroll,
                )

            elif event.type == MOUSEBUTTONDOWN:
                if event.button == 1:
                    self._handle_click(event.pos)

    def update(self):
        """Placeholder for compatibility."""

    def draw(self):
        """Draw viewer on screen."""

        self.image.fill(WINDOW_BG)

        area = (0, self.scroll_offset, self.rect.width, self.rect.height)
        self.image.blit(self.content_surface, (0, 0), area)

        draw_border(self.image)
        blit_on_screen(self.image, self.rect)

    # --- helpers -------------------------------------------------------

    def _handle_click(self, pos):
        """Trigger restoring entry when clicking nodes."""

        if not self.rect.collidepoint(pos):
            return

        local_y = pos[1] - self.rect.top + self.scroll_offset
        local_x = pos[0] - self.rect.left

        for rect, index in self.node_hitboxes:
            if rect.collidepoint(local_x, local_y):
                if self.history.go_to(index):
                    self._render_timeline()
                break

    def _estimate_height(self):
        """Estimate content height for sizing."""

        entries = len(self.history.entries)
        if not entries:
            return 240

        return 120 + ((entries - 1) * self.node_spacing)

    def _render_timeline(self):
        """Render full timeline to content surface."""

        entries = self.history.entries

        content_height = max(self.rect.height, self._estimate_height())
        self.content_surface = render_rect(self.rect.width, content_height, WINDOW_BG)
        draw_border(self.content_surface)

        header = render_text(
            "Graph history - click a node to restore", **HEADER_SETTINGS,
        )
        header_rect = header.get_rect()
        header_rect.topleft = (20, 15)
        self.content_surface.blit(header, header_rect)

        if len(entries) <= 1:
            info = render_text(
                "Interact with the graph to create history entries.",
                **TEXT_SETTINGS,
            )
            info_rect = info.get_rect()
            info_rect.topleft = header_rect.move(0, 40).topleft
            self.content_surface.blit(info, info_rect)
            self.node_hitboxes = []
            self.max_scroll = 0
            return

        self.node_hitboxes = []

        center_x = self.rect.width // 3
        text_x = center_x + self.node_radius + 20
        max_text_width = self.rect.width - text_x - 30

        y = header_rect.bottom + 35

        for index, entry in enumerate(entries):
            center = (center_x, y)

            if index:
                draw_line(
                    self.content_surface,
                    BUTTON_FG,
                    (center_x, y - self.node_spacing + self.node_radius),
                    (center_x, y - self.node_radius),
                    2,
                )

            fill_color = (
                HOVERED_BUTTON_BG if index == self.history.current_index else BUTTON_BG
            )

            draw_circle(self.content_surface, fill_color, center, self.node_radius)
            draw_circle(self.content_surface, BUTTON_FG, center, self.node_radius, 2)

            if entry.saved:
                draw_circle(self.content_surface, WINDOW_FG, center, self.node_radius // 2)

            description = render_text(
                text=f"{index + 1}. {entry.description}",
                max_width=max_text_width,
                **TEXT_SETTINGS,
            )
            description_rect = description.get_rect()
            description_rect.midleft = (text_x, y - 10)
            self.content_surface.blit(description, description_rect)

            time_text = render_text(
                text=entry.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                max_width=max_text_width,
                **TEXT_SETTINGS,
            )
            time_rect = time_text.get_rect()
            time_rect.midleft = (text_x, y + 16)
            self.content_surface.blit(time_text, time_rect)

            hitbox = description_rect.union(time_rect)
            hitbox.union_ip((center_x - self.node_radius, y - self.node_radius, self.node_radius * 2, self.node_radius * 2))
            self.node_hitboxes.append((hitbox, index))

            y += self.node_spacing

        self.max_scroll = max(0, self.content_surface.get_height() - self.rect.height)
        self.scroll_offset = min(self.scroll_offset, self.max_scroll)


def present_history_viewer(history):
    """Instantiate and present viewer."""

    viewer = HistoryViewer(history)
    viewer.present()

