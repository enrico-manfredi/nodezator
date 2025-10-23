"""Facilities to keep and restore versions of the graph."""

### standard library imports

from __future__ import annotations

from copy import deepcopy

from dataclasses import dataclass

from datetime import datetime

from typing import List, Optional


### local imports

from ..config import APP_REFS

from ..our3rdlibs.behaviour import (
    indicate_saved,
    indicate_unsaved,
    set_status_message,
)


@dataclass
class HistoryEntry:
    """Store data for a single history version."""

    data: dict
    timestamp: datetime
    description: str
    saved: bool = False


class GraphHistory:
    """Maintain graph versions and restore them on demand."""

    def __init__(self):
        """Store reference and prepare containers."""

        APP_REFS.history = self

        self._entries: List[HistoryEntry] = []
        self._index: int = -1
        self._snapshot_counter: int = 1
        self._suspended: bool = False

    # --- basic data ----------------------------------------------------

    @property
    def entries(self) -> List[HistoryEntry]:
        """Return recorded entries."""

        return self._entries

    @property
    def current_index(self) -> int:
        """Return index of current entry."""

        return self._index

    # --- recording -----------------------------------------------------

    def reset(
        self,
        data: Optional[dict],
        description: str = "Initial state",
        *,
        saved: bool = True,
    ) -> None:
        """Clear history and optionally prime it with data."""

        self._entries.clear()
        self._index = -1
        self._snapshot_counter = 1

        if data is None:
            return

        entry = HistoryEntry(
            data=deepcopy(data),
            timestamp=datetime.now(),
            description=description,
            saved=saved,
        )

        self._entries.append(entry)
        self._index = 0

    def capture(self, description: Optional[str] = None) -> None:
        """Record current graph data as a new entry, if possible."""

        if self._suspended:
            return

        if not self._entries:
            return

        snapshot = deepcopy(APP_REFS.data)
        current = self._entries[self._index]

        if snapshot == current.data:
            current.saved = False
            return

        del self._entries[self._index + 1 :]

        entry = HistoryEntry(
            data=snapshot,
            timestamp=datetime.now(),
            description=description or self._next_description(),
            saved=False,
        )

        self._entries.append(entry)
        self._index += 1

        set_status_message(f"Recorded {entry.description}")

    def mark_current_saved(self) -> None:
        """Mark current entry as representing the saved state."""

        if not self._entries:
            return

        for entry in self._entries:
            entry.saved = False

        self._entries[self._index].saved = True

    # --- navigation ----------------------------------------------------

    def undo(self) -> bool:
        """Restore previous entry if available."""

        if self._index <= 0:
            set_status_message("Nothing to undo")
            return False

        target = self._index - 1
        self._go_to(target, action="Undo")
        return True

    def redo(self) -> bool:
        """Restore next entry if available."""

        if self._index >= len(self._entries) - 1:
            set_status_message("Nothing to redo")
            return False

        target = self._index + 1
        self._go_to(target, action="Redo")
        return True

    def go_to(self, index: int) -> bool:
        """Restore entry at given index."""

        if index == self._index:
            return True

        if not 0 <= index < len(self._entries):
            return False

        self._go_to(index, action="Restore")
        return True

    # --- presentation --------------------------------------------------

    def present_history(self) -> None:
        """Show viewer containing the recorded history."""

        if not self._entries:
            set_status_message("History not available yet")
            return

        from .historyviewer import present_history_viewer

        present_history_viewer(self)

    # --- helpers -------------------------------------------------------

    def _next_description(self) -> str:
        """Return description for next snapshot."""

        description = f"Change #{self._snapshot_counter}"
        self._snapshot_counter += 1
        return description

    def _go_to(self, index: int, *, action: str) -> None:
        """Restore entry at index and set status message."""

        entry = self._entries[index]
        self._apply_entry(entry)
        self._index = index

        set_status_message(f"{action}: {entry.description}")

    def _apply_entry(self, entry: HistoryEntry) -> None:
        """Replace graph data by the one stored in entry."""

        self._suspended = True

        try:

            gm = APP_REFS.gm

            gm.free_up_memory()
            APP_REFS.data = deepcopy(entry.data)
            gm.prepare_for_new_session()
            APP_REFS.ea.prepare_for_new_session()
            APP_REFS.ea.must_update_birdseye_view_objects = True

            if entry.saved:
                indicate_saved()
            else:
                indicate_unsaved(record=False)

            APP_REFS.wm.draw()

        finally:

            self._suspended = False


__all__ = ("GraphHistory", "HistoryEntry")

