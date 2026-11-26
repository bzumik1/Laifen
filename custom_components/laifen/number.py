"""Number platform for the Laifen integration."""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import override

from laifen_ble import (
    BRUSHING_TIME_STEP,
    MAX_BRUSHING_TIME,
    MAX_SETTING,
    MIN_BRUSHING_TIME,
    MIN_SETTING,
    LaifenState,
    LaifenToothbrush,
)

from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberEntityDescription,
)
from homeassistant.const import EntityCategory, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import LaifenConfigEntry
from .entity import LaifenConnectedEntity, laifen_command

PARALLEL_UPDATES = 1


@dataclass(frozen=True, kw_only=True)
class LaifenNumberEntityDescription(NumberEntityDescription):
    """Describes a Laifen number."""

    value_fn: Callable[[LaifenState], int]
    limits_fn: Callable[[LaifenState], tuple[int, int]] | None = None
    set_fn: Callable[[LaifenToothbrush, int], Awaitable[None]]


NUMBERS: tuple[LaifenNumberEntityDescription, ...] = (
    LaifenNumberEntityDescription(
        key="strength",
        translation_key="strength",
        entity_category=EntityCategory.CONFIG,
        native_min_value=MIN_SETTING,
        native_max_value=MAX_SETTING,
        native_step=1,
        value_fn=lambda state: state.active_mode_settings.strength,
        limits_fn=lambda state: state.mode.strength_limits,
        set_fn=lambda toothbrush, value: toothbrush.set_strength(value),
    ),
    LaifenNumberEntityDescription(
        key="range",
        translation_key="range",
        entity_category=EntityCategory.CONFIG,
        native_min_value=MIN_SETTING,
        native_max_value=MAX_SETTING,
        native_step=1,
        value_fn=lambda state: state.active_mode_settings.range,
        set_fn=lambda toothbrush, value: toothbrush.set_range(value),
    ),
    LaifenNumberEntityDescription(
        key="speed",
        translation_key="speed",
        entity_category=EntityCategory.CONFIG,
        native_min_value=MIN_SETTING,
        native_max_value=MAX_SETTING,
        native_step=1,
        value_fn=lambda state: state.active_mode_settings.speed,
        set_fn=lambda toothbrush, value: toothbrush.set_speed(value),
    ),
    LaifenNumberEntityDescription(
        key="brushing_time",
        translation_key="brushing_time",
        entity_category=EntityCategory.CONFIG,
        device_class=NumberDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        native_min_value=MIN_BRUSHING_TIME,
        native_max_value=MAX_BRUSHING_TIME,
        native_step=BRUSHING_TIME_STEP,
        value_fn=lambda state: state.brushing_time,
        set_fn=lambda toothbrush, value: toothbrush.set_brushing_time(value),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LaifenConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Laifen numbers."""
    coordinator = entry.runtime_data
    async_add_entities(
        LaifenNumber(coordinator, description) for description in NUMBERS
    )


class LaifenNumber(LaifenConnectedEntity, NumberEntity):
    """A setting of the toothbrush."""

    entity_description: LaifenNumberEntityDescription

    @property
    @override
    def native_value(self) -> int | None:
        """Return the value of the setting."""
        state = self.toothbrush.state
        return self.entity_description.value_fn(state) if state else None

    @property
    @override
    def native_min_value(self) -> float:
        """Return the minimum value of the setting."""
        if (limits := self._limits) is None:
            return super().native_min_value
        return limits[0]

    @property
    @override
    def native_max_value(self) -> float:
        """Return the maximum value of the setting."""
        if (limits := self._limits) is None:
            return super().native_max_value
        return limits[1]

    @property
    def _limits(self) -> tuple[int, int] | None:
        """Return the limits that depend on the state of the toothbrush."""
        state = self.toothbrush.state
        if self.entity_description.limits_fn is None or state is None:
            return None
        return self.entity_description.limits_fn(state)

    @override
    @laifen_command
    async def async_set_native_value(self, value: float) -> None:
        """Change the setting."""
        await self.entity_description.set_fn(self.toothbrush, int(value))
