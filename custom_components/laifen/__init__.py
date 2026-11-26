"""The Laifen integration."""

from laifen_ble import LaifenToothbrush

from homeassistant.components.bluetooth import async_ble_device_from_address
from homeassistant.const import CONF_ADDRESS, Platform
from homeassistant.core import HomeAssistant

from .coordinator import LaifenConfigEntry, LaifenCoordinator

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.EVENT,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
]


async def async_setup_entry(hass: HomeAssistant, entry: LaifenConfigEntry) -> None:
    """Set up Laifen from a config entry."""
    address: str = entry.data[CONF_ADDRESS]
    ble_device = async_ble_device_from_address(hass, address, connectable=True)
    coordinator = LaifenCoordinator(
        hass, entry, LaifenToothbrush(ble_device or address)
    )
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)


async def async_unload_entry(hass: HomeAssistant, entry: LaifenConfigEntry) -> None:
    """Unload a config entry."""
    await hass.config_entries.async_unload_platforms_or_raise(entry, PLATFORMS)
