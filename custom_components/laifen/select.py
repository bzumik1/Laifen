"""Select platform for the Laifen integration."""

from typing import override

from laifen_ble import Mode

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import LaifenConfigEntry
from .entity import LaifenConnectedEntity, laifen_command

PARALLEL_UPDATES = 1

MODES = {
    Mode.MODE_1: "mode_1",
    Mode.MODE_2: "mode_2",
    Mode.MODE_3: "mode_3",
    Mode.HIGH_FREQUENCY: "high_frequency",
}
OPTION_MODES = {option: mode for mode, option in MODES.items()}

MODE_DESCRIPTION = SelectEntityDescription(key="mode", translation_key="mode")


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LaifenConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Laifen mode select."""
    async_add_entities([LaifenModeSelect(entry.runtime_data, MODE_DESCRIPTION)])


class LaifenModeSelect(LaifenConnectedEntity, SelectEntity):
    """Select the brushing mode of the toothbrush."""

    @property
    @override
    def options(self) -> list[str]:
        """Return the modes that can be selected."""
        state = self.toothbrush.state
        return [
            option
            for mode, option in MODES.items()
            if mode is not Mode.HIGH_FREQUENCY or (state and state.high_frequency)
        ]

    @property
    @override
    def current_option(self) -> str | None:
        """Return the active mode."""
        state = self.toothbrush.state
        return MODES[state.mode] if state else None

    @override
    @laifen_command
    async def async_select_option(self, option: str) -> None:
        """Select a mode."""
        await self.toothbrush.set_mode(OPTION_MODES[option])
