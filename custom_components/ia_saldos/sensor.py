"""Sensores de saldo."""
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

from .const import (
    DEEPSEEK_SERVICIO,
    DOMAIN,
    NOMBRES_DISPOSITIVO,
    OPENROUTER_SERVICIO,
    PINGEN_SERVICIO,
    UPDATE_INTERVAL,
    URL_CUENTA,
)
from .coordinator import IaSaldosCoordinator


@dataclass(frozen=True, kw_only=True)
class SensorSaldo(SensorEntityDescription):
    """Descripción de un sensor de saldo."""


SENSORES: dict[str, tuple[SensorSaldo, ...]] = {
    OPENROUTER_SERVICIO: (
        SensorSaldo(
            key="credito_clave",
            translation_key="credito_clave",
            name="Crédito de la clave",
            icon="mdi:key-variant",
            native_unit_of_measurement=CURRENCY_DOLLAR,
            device_class=SensorDeviceClass.MONETARY,
            state_class=SensorStateClass.TOTAL,
            suggested_display_precision=2,
        ),
        SensorSaldo(
            key="saldo_cuenta",
            translation_key="saldo_cuenta",
            name="Saldo de la cuenta",
            icon="mdi:cash-multiple",
            native_unit_of_measurement=CURRENCY_DOLLAR,
            device_class=SensorDeviceClass.MONETARY,
            state_class=SensorStateClass.TOTAL,
            suggested_display_precision=2,
        ),
        SensorSaldo(
            key="limite_clave",
            translation_key="limite_clave",
            name="Límite de la clave",
            icon="mdi:speedometer",
            native_unit_of_measurement=CURRENCY_DOLLAR,
            device_class=SensorDeviceClass.MONETARY,
            suggested_display_precision=2,
        ),
        SensorSaldo(
            key="gastado_total",
            translation_key="gastado_total",
            name="Gastado histórico",
            icon="mdi:chart-line",
            native_unit_of_measurement=CURRENCY_DOLLAR,
            device_class=SensorDeviceClass.MONETARY,
            state_class=SensorStateClass.TOTAL_INCREASING,
            suggested_display_precision=2,
            entity_registry_enabled_default=False,
        ),
        SensorSaldo(
            key="gasto_mes",
            translation_key="gasto_mes",
            name="Gastado este mes",
            icon="mdi:calendar-month",
            native_unit_of_measurement=CURRENCY_DOLLAR,
            device_class=SensorDeviceClass.MONETARY,
            state_class=SensorStateClass.TOTAL,
            suggested_display_precision=2,
        ),
        SensorSaldo(
            key="gasto_hoy",
            translation_key="gasto_hoy",
            name="Gastado hoy",
            icon="mdi:clock-outline",
            native_unit_of_measurement=CURRENCY_DOLLAR,
            device_class=SensorDeviceClass.MONETARY,
            state_class=SensorStateClass.TOTAL,
            suggested_display_precision=4,
        ),
        SensorSaldo(
            key="creditos_comprados",
            translation_key="creditos_comprados",
            name="Créditos comprados",
            icon="mdi:credit-card-plus",
            native_unit_of_measurement=CURRENCY_DOLLAR,
            device_class=SensorDeviceClass.MONETARY,
            state_class=SensorStateClass.TOTAL_INCREASING,
            suggested_display_precision=2,
            entity_registry_enabled_default=False,
        ),
    ),
    DEEPSEEK_SERVICIO: (
        SensorSaldo(
            key="saldo",
            translation_key="saldo",
            name="Saldo",
            icon="mdi:cash",
            native_unit_of_measurement=CURRENCY_DOLLAR,
            device_class=SensorDeviceClass.MONETARY,
            state_class=SensorStateClass.TOTAL,
            suggested_display_precision=2,
        ),
        SensorSaldo(
            key="recargado",
            translation_key="recargado",
            name="Saldo recargado",
            icon="mdi:wallet",
            native_unit_of_measurement=CURRENCY_DOLLAR,
            device_class=SensorDeviceClass.MONETARY,
            state_class=SensorStateClass.TOTAL,
            suggested_display_precision=2,
        ),
        SensorSaldo(
            key="regalo",
            translation_key="regalo",
            name="Saldo de regalo",
            icon="mdi:gift",
            native_unit_of_measurement=CURRENCY_DOLLAR,
            device_class=SensorDeviceClass.MONETARY,
            state_class=SensorStateClass.TOTAL,
            suggested_display_precision=2,
            entity_registry_enabled_default=False,
        ),
    ),
    PINGEN_SERVICIO: (
        SensorSaldo(
            key="saldo",
            translation_key="pingen_saldo",
            name="Saldo",
            icon="mdi:cash",
            # la moneda la pone la API (CHF), se resuelve en la entidad
            suggested_display_precision=2,
        ),
        SensorSaldo(
            key="faltante",
            translation_key="pingen_faltante",
            name="Créditos que faltan",
            icon="mdi:alert-circle-outline",
            suggested_display_precision=2,
            entity_registry_enabled_default=False,
        ),
        SensorSaldo(
            key="plan",
            translation_key="pingen_plan",
            name="Plan",
            icon="mdi:tag-outline",
        ),
    ),
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Crea los sensores de cada servicio configurado."""
    coordinador: IaSaldosCoordinator = hass.data[DOMAIN][entry.entry_id]
    entidades: list[SensorEntity] = []

    for servicio, descripciones in SENSORES.items():
        for descripcion in descripciones:
            entidades.append(SensorSaldoIA(coordinador, entry, servicio, descripcion))

    async_add_entities(entidades)


class SensorSaldoIA(CoordinatorEntity[IaSaldosCoordinator], SensorEntity):
    """Un dato de saldo de un servicio."""

    _attr_has_entity_name = True
    entity_description: SensorSaldo

    def __init__(
        self,
        coordinador: IaSaldosCoordinator,
        entry: ConfigEntry,
        servicio: str,
        descripcion: SensorSaldo,
    ) -> None:
        super().__init__(coordinador)
        self.entity_description = descripcion
        self._servicio = servicio
        self._attr_unique_id = f"{entry.entry_id}_{servicio}_{descripcion.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{entry.entry_id}_{servicio}")},
            name=NOMBRES_DISPOSITIVO[servicio]["name"],
            manufacturer=NOMBRES_DISPOSITIVO[servicio]["manufacturer"],
            model=NOMBRES_DISPOSITIVO[servicio]["model"],
            entry_type=DeviceEntryType.SERVICE,
            configuration_url=URL_CUENTA.get(servicio),
        )

    @property
    def native_unit_of_measurement(self):
        """Pingen devuelve la moneda en cada consulta (CHF, EUR...)."""
        if (
            self._servicio == PINGEN_SERVICIO
            and self.entity_description.key == "saldo"
        ):
            datos = (self.coordinator.data or {}).get(PINGEN_SERVICIO) or {}
            return datos.get("moneda") or None
        return self.entity_description.native_unit_of_measurement

    @property
    def native_value(self):
        """Valor del sensor, o None si el servicio no respondió."""
        datos = (self.coordinator.data or {}).get(self._servicio) or {}
        return datos.get(self.entity_description.key)

    @property
    def available(self) -> bool:
        """Disponible solo si hay dato de ESTE servicio."""
        return (
            self.coordinator.last_update_success
            and (self.coordinator.data or {}).get(self._servicio) is not None
        )

    @property
    def extra_state_attributes(self) -> dict:
        """Notas útiles para la UI."""
        atributos = {"cada_minutos": UPDATE_INTERVAL}
        if self._servicio == PINGEN_SERVICIO:
            datos = (self.coordinator.data or {}).get(PINGEN_SERVICIO) or {}
            for clave in ("organizacion", "estado", "facturacion", "moneda"):
                if datos.get(clave):
                    atributos[clave] = datos[clave]
        return atributos
