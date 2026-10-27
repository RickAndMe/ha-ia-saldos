"""Sensores de saldo y de suscripción."""
from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CURRENCY_DOLLAR
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CLAVES, DISPOSITIVOS, DOMAIN
from .coordinator import ServicioCoordinator


@dataclass(frozen=True, kw_only=True)
class SensorSaldo(SensorEntityDescription):
    """Descripción de un sensor."""


NOMBRE_CLAVE = "dinero"


SENSORES: dict[str, tuple[SensorSaldo, ...]] = {
    "openrouter": (
        SensorSaldo(
            key="credito_clave", translation_key="credito_clave",
            name="Crédito de la clave", icon="mdi:key-variant",
            native_unit_of_measurement=CURRENCY_DOLLAR,
            device_class=SensorDeviceClass.MONETARY,
            state_class=SensorStateClass.TOTAL, suggested_display_precision=2,
        ),
        SensorSaldo(
            key="saldo_cuenta", translation_key="saldo_cuenta",
            name="Saldo de la cuenta", icon="mdi:cash-multiple",
            native_unit_of_measurement=CURRENCY_DOLLAR,
            device_class=SensorDeviceClass.MONETARY,
            state_class=SensorStateClass.TOTAL, suggested_display_precision=2,
        ),
        SensorSaldo(
            key="limite_clave", translation_key="limite_clave",
            name="Límite de la clave", icon="mdi:speedometer",
            native_unit_of_measurement=CURRENCY_DOLLAR,
            device_class=SensorDeviceClass.MONETARY, suggested_display_precision=2,
        ),
        SensorSaldo(
            key="gastado_total", translation_key="gastado_total",
            name="Gastado histórico", icon="mdi:chart-line",
            native_unit_of_measurement=CURRENCY_DOLLAR,
            device_class=SensorDeviceClass.MONETARY,
            state_class=SensorStateClass.TOTAL_INCREASING,
            suggested_display_precision=2, entity_registry_enabled_default=False,
        ),
        SensorSaldo(
            key="gasto_mes", translation_key="gasto_mes",
            name="Gastado este mes", icon="mdi:calendar-month",
            native_unit_of_measurement=CURRENCY_DOLLAR,
            device_class=SensorDeviceClass.MONETARY,
            state_class=SensorStateClass.TOTAL, suggested_display_precision=2,
        ),
        SensorSaldo(
            key="gasto_hoy", translation_key="gasto_hoy",
            name="Gastado hoy", icon="mdi:clock-outline",
            native_unit_of_measurement=CURRENCY_DOLLAR,
            device_class=SensorDeviceClass.MONETARY,
            state_class=SensorStateClass.TOTAL, suggested_display_precision=4,
        ),
        SensorSaldo(
            key="creditos_comprados", translation_key="creditos_comprados",
            name="Créditos comprados", icon="mdi:credit-card-plus",
            native_unit_of_measurement=CURRENCY_DOLLAR,
            device_class=SensorDeviceClass.MONETARY,
            state_class=SensorStateClass.TOTAL_INCREASING,
            suggested_display_precision=2, entity_registry_enabled_default=False,
        ),
    ),
    "deepseek": (
        SensorSaldo(
            key="saldo", translation_key="saldo",
            name="Saldo", icon="mdi:cash",
            native_unit_of_measurement=CURRENCY_DOLLAR,
            device_class=SensorDeviceClass.MONETARY,
            state_class=SensorStateClass.TOTAL, suggested_display_precision=2,
        ),
        SensorSaldo(
            key="recargado", translation_key="recargado",
            name="Saldo recargado", icon="mdi:wallet",
            native_unit_of_measurement=CURRENCY_DOLLAR,
            device_class=SensorDeviceClass.MONETARY,
            state_class=SensorStateClass.TOTAL, suggested_display_precision=2,
        ),
        SensorSaldo(
            key="regalo", translation_key="regalo",
            name="Saldo de regalo", icon="mdi:gift",
            native_unit_of_measurement=CURRENCY_DOLLAR,
            device_class=SensorDeviceClass.MONETARY,
            state_class=SensorStateClass.TOTAL, suggested_display_precision=2,
            entity_registry_enabled_default=False,
        ),
    ),
    "realdebrid": (
        SensorSaldo(
            key="dias_restantes", translation_key="dias_restantes",
            name="Días que quedan", icon="mdi:calendar-clock",
            native_unit_of_measurement="d", suggested_display_precision=0,
        ),
        SensorSaldo(
            key="caduca", translation_key="caduca",
            name="Caduca el", icon="mdi:calendar-end",
            device_class=SensorDeviceClass.TIMESTAMP,
        ),
        SensorSaldo(
            key="puntos", translation_key="puntos",
            name="Puntos de fidelidad", icon="mdi:star-circle-outline",
        ),
    ),
    "alldebrid": (
        SensorSaldo(
            key="dias_restantes", translation_key="dias_restantes",
            name="Días que quedan", icon="mdi:calendar-clock",
            native_unit_of_measurement="d", suggested_display_precision=0,
        ),
        SensorSaldo(
            key="caduca", translation_key="caduca",
            name="Caduca el", icon="mdi:calendar-end",
            device_class=SensorDeviceClass.TIMESTAMP,
        ),
        SensorSaldo(
            key="puntos", translation_key="puntos",
            name="Puntos de fidelidad", icon="mdi:star-circle-outline",
        ),
    ),
    "torbox": (
        SensorSaldo(
            key="dias_restantes", translation_key="dias_restantes",
            name="Días que quedan", icon="mdi:calendar-clock",
            native_unit_of_measurement="d", suggested_display_precision=0,
        ),
        SensorSaldo(
            key="caduca", translation_key="caduca",
            name="Caduca el", icon="mdi:calendar-end",
            device_class=SensorDeviceClass.TIMESTAMP,
        ),
    ),
}


def _dispositivo(entry: ConfigEntry, servicio: str) -> DeviceInfo:
    info = DISPOSITIVOS[servicio]
    return DeviceInfo(
        identifiers={(DOMAIN, f"{entry.entry_id}_{servicio}")},
        name=info["name"],
        manufacturer=info["manufacturer"],
        model=info["model"],
        entry_type=DeviceEntryType.SERVICE,
        configuration_url=info["url"],
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Crea los sensores de cada servicio configurado."""
    coordinadores: dict[str, ServicioCoordinator] = hass.data[DOMAIN][entry.entry_id]
    entidades: list[SensorEntity] = []

    for servicio, coordinador in coordinadores.items():
        for descripcion in SENSORES.get(servicio, ()):
            entidades.append(SensorServicio(coordinador, entry, servicio, descripcion))

    async_add_entities(entidades)


class SensorServicio(CoordinatorEntity[ServicioCoordinator], SensorEntity):
    """Un dato de un servicio (saldo, caducidad, puntos...)."""

    _attr_has_entity_name = True
    entity_description: SensorSaldo

    def __init__(
        self,
        coordinador: ServicioCoordinator,
        entry: ConfigEntry,
        servicio: str,
        descripcion: SensorSaldo,
    ) -> None:
        super().__init__(coordinador)
        self.entity_description = descripcion
        self._servicio = servicio
        self._attr_unique_id = f"{entry.entry_id}_{servicio}_{descripcion.key}"
        self._attr_device_info = _dispositivo(entry, servicio)

    @property
    def native_value(self):
        """Valor del sensor, o None si no hay dato."""
        datos = self.coordinator.data or {}
        return datos.get(self.entity_description.key)

    @property
    def available(self) -> bool:
        return self.coordinator.last_update_success and bool(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict:
        """Cuenta y frecuencia de consulta."""
        datos = self.coordinator.data or {}
        atributos = {"cada_minutos": self.coordinator.servicio_minutos}
        if datos.get("usuario"):
            atributos["cuenta"] = datos["usuario"]
        if datos.get("tipo_cuenta"):
            atributos["tipo"] = datos["tipo_cuenta"]
        return atributos
