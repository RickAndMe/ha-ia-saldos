"""Configuración por interfaz (alta y edición)."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CLAVES,
    DOMAIN,
    TIMEOUT,
    URL_ALDEBRID_USER,
    URL_DEEPSEEK_SALDO,
    URL_OPENROUTER_CREDITOS,
    URL_REALDEBRID_USER,
    URL_TORBOX_USER,
)

_LOGGER = logging.getLogger(__name__)

URL_PRUEBA = {
    "openrouter": URL_OPENROUTER_CREDITOS,
    "deepseek": URL_DEEPSEEK_SALDO,
    "realdebrid": URL_REALDEBRID_USER,
    "alldebrid": URL_ALDEBRID_USER,
    "torbox": URL_TORBOX_USER,
}

ESQUEMA = vol.Schema(
    {
        vol.Optional("openrouter_key"): str,
        vol.Optional("deepseek_key"): str,
        vol.Optional("realdebrid_key"): str,
        vol.Optional("alldebrid_key"): str,
        vol.Optional("torbox_key"): str,
    }
)


async def _prueba(sesion, servicio: str, clave: str) -> bool:
    """Comprueba que la clave responde 200 en su API."""
    try:
        async with asyncio.timeout(TIMEOUT):
            async with sesion.get(
                URL_PRUEBA[servicio],
                headers={"Authorization": f"Bearer {clave}", "Accept": "application/json"},
            ) as resp:
                return resp.status == 200
    except Exception:  # noqa: BLE001
        return False


async def _valida(sesion, user_input: dict[str, Any]) -> tuple[dict[str, str], dict[str, str]]:
    """Devuelve (claves_válidas, errores)."""
    validas: dict[str, str] = {}
    errores: dict[str, str] = {}
    for servicio, campo in CLAVES.items():
        valor = (user_input.get(campo) or "").strip()
        if not valor:
            continue
        if await _prueba(sesion, servicio, valor):
            validas[campo] = valor
        else:
            errores[campo] = "clave_invalida"
    return validas, errores


class IaSaldosConfigFlow(ConfigFlow, domain=DOMAIN):
    """Alta desde la UI."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errores: dict[str, str] = {}

        if user_input is not None:
            sesion = async_get_clientsession(self.hass)
            validas, errores = await _valida(sesion, user_input)
            if not validas and not errores:
                errores["base"] = "sin_claves"
            if not errores and validas:
                return self.async_create_entry(title="Cuentas de IA y debrid", data=validas)

        return self.async_show_form(step_id="user", data_schema=ESQUEMA, errors=errores)

    @staticmethod
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return IaSaldosOptionsFlow()


class IaSaldosOptionsFlow(OptionsFlow):
    """Añadir o cambiar claves en una instalación existente."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errores: dict[str, str] = {}

        if user_input is not None:
            sesion = async_get_clientsession(self.hass)
            validas, errores = await _valida(sesion, user_input)
            if not errores:
                actuales = {**self.config_entry.data, **self.config_entry.options}
                actuales.update(validas)
                return self.async_create_entry(title="", data=actuales)

        return self.async_show_form(step_id="init", data_schema=ESQUEMA, errors=errores)
