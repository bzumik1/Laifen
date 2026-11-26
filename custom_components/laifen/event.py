"""Event platform for the Laifen integration."""

from typing import override

from homeassistant.components.event import EventEntity, EventEntityDescription
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import LaifenConfigEntry, LaifenCoordinator
from .entity import LaifenEntity

PARALLEL_UPDATES = 0

BRUSHING_FINISHED = "brushing_finished"

BRUSHING_DESCRIPTION = EventEntityDescription(
    key="brushing_session",
    translation_key="brushing_session",
    event_types=[BRUSHING_FINISHED],
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LaifenConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Laifen brushing event."""
    async_add_entities([LaifenBrushingEvent(entry.runtime_data, BRUSHING_DESCRIPTION)])


class LaifenBrushingEvent(LaifenEntity, EventEntity):
    """Fires when a brushing session finishes."""

    def __init__(
        self,
        coordinator: LaifenCoordinator,
        entity_description: EventEntityDescription,
    ) -> None:
        """Initialize the event."""
        super().__init__(coordinator, entity_description)
        self._last_session = coordinator.toothbrush.last_session

    @callback
    @override
    def _handle_coordinator_update(self) -> None:
        """Fire the event when a new session finished."""
        session = self.toothbrush.last_session
        if session is not None and session is not self._last_session:
            self._last_session = session
            self._trigger_event(BRUSHING_FINISHED, {"duration": session.duration})
            super()._handle_coordinator_update()
