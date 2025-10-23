
### standard library imports
from warnings import catch_warnings, simplefilter


### third-party imports

from pygame.locals import RESIZABLE

from pygame.version import vernum as pygame_vernum

from pygame.display import set_mode

from pygame.event import get as pygame_get_events, set_allowed

from pygame.key import (
    get_pressed as get_pressed_keys,
    get_mods as get_pressed_mod_keys,
    stop_text_input,
)

from pygame.mouse import (
    set_visible as set_mouse_visibility,
    get_pos as pygame_get_pos,
    set_pos as pygame_set_pos,
    get_pressed as get_mouse_pressed,
)

from pygame.display import update as pygame_update
from pygame.locals import MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION
from pygame.math import Vector2


### local imports

from ..constants import (
    SCREEN,
    SCREEN_RECT,
    SIZE,
    GENERAL_NS,
    GENERAL_SERVICE_NAMES,
    FPS,
    maintain_fps,
    watch_window_size,
)

from ...config import APP_REFS


EDITING_STATES = {
    'loaded_file',
    'moving_object',
    'segment_definition',
    'segment_severance',
    'box_selection',
    'birdseye_view',
}


def _should_apply_zoom():
    zoom_manager = getattr(APP_REFS, 'zoom_manager', None)
    window_manager = getattr(APP_REFS, 'wm', None)

    return (
        zoom_manager is not None
        and window_manager is not None
        and getattr(window_manager, 'state_name', '') in EDITING_STATES
        and zoom_manager.scale != 1.0
    )


def _convert_to_int_pair(vector):
    return int(round(vector.x)), int(round(vector.y))


def get_events():
    events = pygame_get_events()

    if not events:
        return events

    if not _should_apply_zoom():
        return events

    zoom_manager = APP_REFS.zoom_manager

    for event in events:
        if event.type in (MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION):
            adjusted = zoom_manager.screen_to_world(Vector2(event.pos))
            event.pos = _convert_to_int_pair(adjusted)

    return events


def get_mouse_pos():
    pos = Vector2(pygame_get_pos())

    if _should_apply_zoom():
        pos = APP_REFS.zoom_manager.screen_to_world(pos)

    return _convert_to_int_pair(pos)


def set_mouse_pos(pos):
    target = Vector2(pos)

    if _should_apply_zoom():
        target = APP_REFS.zoom_manager.world_to_screen(target)

    pygame_set_pos(_convert_to_int_pair(target))



### create and use function to activate normal behaviour

def set_behaviour(services_namespace, reset_window_mode=True):
    """Setup normal mode."""
    ### set normal services as current ones.

    our_globals = globals()

    for attr_name in GENERAL_SERVICE_NAMES:

        value = our_globals[attr_name]
        setattr(services_namespace, attr_name, value)

    ### allow all kinds of events (by passing None to
    ### pygame.event.set_allowed), except text input ones (by
    ### stopping text input events),
    ### which should be enabled only when appropriate

    set_allowed(None)
    stop_text_input()

    ### reset window mode if requested

    if reset_window_mode:

        ### use pygame.display.set_mode

        ## under the circumstances in the if-block below, set_mode() raises
        ## a warning that shouldn't be raised (as explained in issue #3385 of
        ## pygame-ce's repository), so we make the call in a context that
        ## temporarily suppresses warnings

        if SIZE == (0, 0) and pygame_vernum in ((2, 5, 2), (2, 5, 3)):

            with catch_warnings():
                simplefilter('ignore')
                set_mode(SIZE, RESIZABLE)

        ## otherwise we can make the call normally

        else:
            set_mode(SIZE, RESIZABLE)

        ## perform setups related to window size
        watch_window_size()



def frame_checkups():
    """Perform various checkups.

    Meant to be used at the beginning of each frame in the
    app loop.
    """
    ### keep a constants framerate
    maintain_fps(FPS)

    ### increment frame number
    GENERAL_NS.frame_index += 1

    ### keep an eye on the window size
    watch_window_size()

def frame_checkups_with_fps(fps):
    """Same as frame_checkups(), but uses given fps."""
    ### keep a constants framerate
    maintain_fps(fps)

    ### increment frame number
    GENERAL_NS.frame_index += 1

    ### keep an eye on the window size
    watch_window_size()


def update_screen():
    zoom_manager = getattr(APP_REFS, 'zoom_manager', None)

    if zoom_manager is not None and _should_apply_zoom():
        zoom_manager.apply(SCREEN)

    pygame_update()
