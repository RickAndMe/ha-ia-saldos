"""Interruptores binarios: ¿tengo premium?"""
from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, SERVICIOS_DEBRID
from .coordinator import ServicioCoordinator
from .sensor import _dispositivo


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Un binario 'premium' por cada servicio debrid configurado."""
    coordinadores: dict[str, ServicioCoordinator] = hass.data[DOMAIN][entry.entry_id]
    entidades = [
        PremiumDebrid(coordinador, entry, servicio)
        for servicio, coordinador in coordinadores.items()
        if servicio in SERVICIOS_DEBRID
    ]
    async_add_entities(entidades)


class PremiumDebrid(CoordinatorEntity[ServicioCoordinator], BinarySensorEntity):
    """Verdadero mientras la cuenta tenga premium activo."""

    _attr_has_entity_name = True
    _attr_translation_key = "premium"
    _attr_icon = "mdi:crown"

    def __init__(
        self,
        coordinador: ServicioCoordinator,
        entry: ConfigEntry,
        servicio: str,
    ) -> None:
        super().__init__(coordinador)
        self._servicio = servicio
        self._attr_unique_id = f"{entry.entry_id}_{servicio}_premium"
        self._attr_device_info = _dispositivo(entry, servicio)

    @property
    def is_on(self) -> bool:
        return bool((self.coordinator.data or {}).get("premium"))

    @property
    def available(self) -> bool:
        return self.coordinator.last_update_success and bool(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict:
        datos = self.coordinator.data or {}
        return {
            "dias_restantes": datos.get("dias_restantes"),
            "caduca": datos.get("caduca").isoformat() if datos.get("caduca") else None,
            "tipo": datos.get("tipo_cuenta"),
        }
