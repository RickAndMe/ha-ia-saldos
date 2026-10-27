"""Configuración por interfaz."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_DEEPSEEK,
    CONF_OPENROUTER,
    DOMAIN,
    TIMEOUT,
    URL_DEEPSEEK_SALDO,
    URL_OPENROUTER_CREDITOS,
)

_LOGGER = logging.getLogger(__name__)

ESQUEMA = vol.Schema(
    {
        vol.Optional(CONF_OPENROUTER): str,
        vol.Optional(CONF_DEEPSEEK): str,
    }
)


async def _prueba(sesion, url: str, clave: str) -> bool:
    """Comprueba que la clave responde 200 sin lanzar errores a la UI."""
    try:
        async with asyncio.timeout(TIMEOUT):
            async with sesion.get(
                url,
                headers={"Authorization": f"Bearer {clave}", "Accept": "application/json"},
            ) as resp:
                return resp.status == 200
    except (TimeoutError, asyncio.TimeoutError, Exception):  # noqa: B014
        return False


class IaSaldosConfigFlow(ConfigFlow, domain=DOMAIN):
    """Alta desde la UI."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errores: dict[str, str] = {}

        if user_input is not None:
            clave_or = (user_input.get(CONF_OPENROUTER) or "").strip()
            clave_ds = (user_input.get(CONF_DEEPSEEK) or "").strip()

            if not clave_or and not clave_ds:
                errores["base"] = "sin_claves"
            else:
                sesion = async_get_clientsession(self.hass)
                if clave_or and not await _prueba(sesion, URL_OPENROUTER_CREDITOS, clave_or):
                    errores[CONF_OPENROUTER] = "clave_invalida"
                if clave_ds and not await _prueba(sesion, URL_DEEPSEEK_SALDO, clave_ds):
                    errores[CONF_DEEPSEEK] = "clave_invalida"

            if not errores:
                datos: dict[str, str] = {}
                if clave_or:
                    datos[CONF_OPENROUTER] = clave_or
                if clave_ds:
                    datos[CONF_DEEPSEEK] = clave_ds
                return self.async_create_entry(title="Saldos de IA", data=datos)

        return self.async_show_form(step_id="user", data_schema=ESQUEMA, errors=errores)
