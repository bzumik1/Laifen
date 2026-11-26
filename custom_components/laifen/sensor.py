"""Sensor platform for the Laifen integration."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import override

from laifen_ble import LaifenState, Mode

from homeassistant.components.sensor import (
    RestoreSensor,
    SensorDeviceClass,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.typing import StateType

from .coordinator import LaifenConfigEntry
from .entity import LaifenEntity

PARALLEL_UPDATES = 0

MODES = {
    Mode.MODE_1: "mode_1",
    Mode.MODE_2: "mode_2",
    Mode.MODE_3: "mode_3",
    Mode.HIGH_FREQUENCY: "high_frequency",
}


@dataclass(frozen=True, kw_only=True)
class LaifenSensorEntityDescription(SensorEntityDescription):
    """Describes a Laifen sensor."""

    value_fn: Callable[[LaifenState], StateType]
    available_while_asleep: bool


SENSORS: tuple[LaifenSensorEntityDescription, ...] = (
    LaifenSensorEntityDescription(
        key="battery",
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda state: state.battery_level,
        available_while_asleep=True,
    ),
    LaifenSensorEntityDescription(
        key="status",
        translation_key="status",
        device_class=SensorDeviceClass.ENUM,
        options=["idle", "brushing"],
        value_fn=lambda state: "brushing" if state.running else "idle",
        available_while_asleep=False,
    ),
    LaifenSensorEntityDescription(
        key="mode",
        translation_key="mode",
        device_class=SensorDeviceClass.ENUM,
        options=list(MODES.values()),
        value_fn=lambda state: MODES[state.mode],
        available_while_asleep=True,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LaifenConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Laifen sensors."""
    coordinator = entry.runtime_data
    async_add_entities(
        LaifenSensor(coordinator, description) for description in SENSORS
    )


class LaifenSensor(LaifenEntity, RestoreSensor):
    """A Laifen sensor that keeps its last value while the toothbrush sleeps."""

    entity_description: LaifenSensorEntityDescription

    @override
    async def async_added_to_hass(self) -> None:
        """Restore the last value."""
        await super().async_added_to_hass()
        if self.entity_description.available_while_asleep and (
            last_sensor_data := await self.async_get_last_sensor_data()
        ):
            self._attr_native_value = last_sensor_data.native_value
        self._update_native_value()

    @callback
    @override
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the toothbrush."""
        self._update_native_value()
        super()._handle_coordinator_update()

    def _update_native_value(self) -> None:
        """Update the value from the last known state of the toothbrush."""
        if (state := self.coordinator.toothbrush.state) is not None:
            self._attr_native_value = self.entity_description.value_fn(state)

    @property
    @override
    def available(self) -> bool:
        """Return whether the sensor is available."""
        return super().available and (
            self.coordinator.toothbrush.connected
            or (
                self.entity_description.available_while_asleep
                and self.native_value is not None
            )
        )
