"""Binary sensor platform for the Laifen integration."""

from typing import override

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import LaifenConfigEntry
from .entity import LaifenConnectedEntity

PARALLEL_UPDATES = 0

AIRPLANE_MODE_DESCRIPTION = BinarySensorEntityDescription(
    key="airplane_mode",
    translation_key="airplane_mode",
    entity_category=EntityCategory.DIAGNOSTIC,
    entity_registry_enabled_default=False,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LaifenConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Laifen binary sensors."""
    async_add_entities(
        [LaifenAirplaneModeSensor(entry.runtime_data, AIRPLANE_MODE_DESCRIPTION)]
    )


class LaifenAirplaneModeSensor(LaifenConnectedEntity, BinarySensorEntity):
    """Whether the airplane mode of the toothbrush is on."""

    @property
    @override
    def is_on(self) -> bool | None:
        """Return whether the airplane mode is on."""
        state = self.toothbrush.state
        return state.airplane_mode if state else None
