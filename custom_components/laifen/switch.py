"""Switch platform for the Laifen integration."""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, override

from laifen_ble import LaifenState, LaifenToothbrush

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import LaifenConfigEntry
from .entity import LaifenConnectedEntity, laifen_command

PARALLEL_UPDATES = 1


@dataclass(frozen=True, kw_only=True)
class LaifenSwitchEntityDescription(SwitchEntityDescription):
    """Describes a Laifen switch."""

    is_on_fn: Callable[[LaifenState], bool]
    set_fn: Callable[[LaifenToothbrush, bool], Awaitable[None]]


SWITCHES: tuple[LaifenSwitchEntityDescription, ...] = (
    LaifenSwitchEntityDescription(
        key="brushing",
        translation_key="brushing",
        is_on_fn=lambda state: state.running,
        set_fn=lambda toothbrush, on: toothbrush.start() if on else toothbrush.stop(),
    ),
    LaifenSwitchEntityDescription(
        key="high_frequency",
        translation_key="high_frequency",
        entity_category=EntityCategory.CONFIG,
        is_on_fn=lambda state: state.high_frequency,
        set_fn=lambda toothbrush, on: toothbrush.set_high_frequency(on),
    ),
    LaifenSwitchEntityDescription(
        key="reminder_30s",
        translation_key="reminder_30s",
        entity_category=EntityCategory.CONFIG,
        is_on_fn=lambda state: state.reminder_30s,
        set_fn=lambda toothbrush, on: toothbrush.set_reminder_30s(on),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LaifenConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Laifen switches."""
    coordinator = entry.runtime_data
    async_add_entities(
        LaifenSwitch(coordinator, description) for description in SWITCHES
    )


class LaifenSwitch(LaifenConnectedEntity, SwitchEntity):
    """A switch of the toothbrush."""

    entity_description: LaifenSwitchEntityDescription

    @property
    @override
    def is_on(self) -> bool | None:
        """Return whether the switch is on."""
        state = self.toothbrush.state
        return self.entity_description.is_on_fn(state) if state else None

    @override
    @laifen_command
    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        await self.entity_description.set_fn(self.toothbrush, True)

    @override
    @laifen_command
    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        await self.entity_description.set_fn(self.toothbrush, False)
