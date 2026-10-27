"""Configuración por interfaz."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_DEEPSEEK,
    CONF_OPENROUTER,
    CONF_PINGEN_ID,
    CONF_PINGEN_SECRET,
    DOMAIN,
    PINGEN_SCOPE,
    TIMEOUT,
    URL_DEEPSEEK_SALDO,
    URL_OPENROUTER_CREDITOS,
    URL_PINGEN_ORGANIZACIONES,
    URL_PINGEN_TOKEN,
)

_LOGGER = logging.getLogger(__name__)

ESQUEMA = vol.Schema(
    {
        vol.Optional(CONF_OPENROUTER): str,
        vol.Optional(CONF_DEEPSEEK): str,
        vol.Optional(CONF_PINGEN_ID): str,
        vol.Optional(CONF_PINGEN_SECRET): str,
    }
)

# en opciones, lo que se deja en blanco no se toca
ESQUEMA_OPCIONES = vol.Schema(
    {
        vol.Optional(CONF_OPENROUTER): str,
        vol.Optional(CONF_DEEPSEEK): str,
        vol.Optional(CONF_PINGEN_ID): str,
        vol.Optional(CONF_PINGEN_SECRET): str,
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


async def _prueba_pingen(sesion, client_id: str, client_secret: str) -> bool:
    """Pingen: pide token y luego las organizaciones (scope organisation_read)."""
    try:
        async with asyncio.timeout(TIMEOUT):
            async with sesion.post(
                URL_PINGEN_TOKEN,
                data={
                    "grant_type": "client_credentials",
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "scope": PINGEN_SCOPE,
                },
            ) as resp:
                if resp.status != 200:
                    return False
                token = (await resp.json(content_type=None)).get("access_token")
            if not token:
                return False
            async with sesion.get(
                URL_PINGEN_ORGANIZACIONES,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.api+json",
                },
            ) as orgs:
                return orgs.status == 200
    except (TimeoutError, asyncio.TimeoutError, Exception):  # noqa: B014
        return False


class IaSaldosConfigFlow(ConfigFlow, domain=DOMAIN):
    """Alta desde la UI."""

    VERSION = 1

    @staticmethod
    def async_get_options_flow(config_entry) -> OptionsFlow:
        return IaSaldosOptionsFlow()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errores: dict[str, str] = {}

        if user_input is not None:
            clave_or = (user_input.get(CONF_OPENROUTER) or "").strip()
            clave_ds = (user_input.get(CONF_DEEPSEEK) or "").strip()
            pingen_id = (user_input.get(CONF_PINGEN_ID) or "").strip()
            pingen_secret = (user_input.get(CONF_PINGEN_SECRET) or "").strip()

            if not clave_or and not clave_ds and not (pingen_id and pingen_secret):
                errores["base"] = "sin_claves"
            else:
                sesion = async_get_clientsession(self.hass)
                if clave_or and not await _prueba(sesion, URL_OPENROUTER_CREDITOS, clave_or):
                    errores[CONF_OPENROUTER] = "clave_invalida"
                if clave_ds and not await _prueba(sesion, URL_DEEPSEEK_SALDO, clave_ds):
                    errores[CONF_DEEPSEEK] = "clave_invalida"
                if pingen_id or pingen_secret:
                    if not (pingen_id and pingen_secret):
                        errores["base"] = "pingen_incompleto"
                    elif not await _prueba_pingen(sesion, pingen_id, pingen_secret):
                        errores[CONF_PINGEN_SECRET] = "clave_invalida"

            if not errores:
                datos: dict[str, str] = {}
                if clave_or:
                    datos[CONF_OPENROUTER] = clave_or
                if clave_ds:
                    datos[CONF_DEEPSEEK] = clave_ds
                if pingen_id and pingen_secret:
                    datos[CONF_PINGEN_ID] = pingen_id
                    datos[CONF_PINGEN_SECRET] = pingen_secret
                return self.async_create_entry(title="Saldos", data=datos)

        return self.async_show_form(step_id="user", data_schema=ESQUEMA, errors=errores)


class IaSaldosOptionsFlow(OptionsFlow):
    """Cambiar o añadir claves sin recrear la integración."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errores: dict[str, str] = {}

        if user_input is not None:
            nuevos = dict(self.config_entry.options)
            sesion = async_get_clientsession(self.hass)

            for campo, url in (
                (CONF_OPENROUTER, URL_OPENROUTER_CREDITOS),
                (CONF_DEEPSEEK, URL_DEEPSEEK_SALDO),
            ):
                valor = (user_input.get(campo) or "").strip()
                if valor:
                    if await _prueba(sesion, url, valor):
                        nuevos[campo] = valor
                    else:
                        errores[campo] = "clave_invalida"

            pingen_id = (user_input.get(CONF_PINGEN_ID) or "").strip()
            pingen_secret = (user_input.get(CONF_PINGEN_SECRET) or "").strip()
            if pingen_id or pingen_secret:
                if not (pingen_id and pingen_secret):
                    errores["base"] = "pingen_incompleto"
                elif await _prueba_pingen(sesion, pingen_id, pingen_secret):
                    nuevos[CONF_PINGEN_ID] = pingen_id
                    nuevos[CONF_PINGEN_SECRET] = pingen_secret
                else:
                    errores[CONF_PINGEN_SECRET] = "clave_invalida"

            if not errores:
                return self.async_create_entry(title="", data=nuevos)

        return self.async_show_form(
            step_id="init", data_schema=ESQUEMA_OPCIONES, errors=errores
        )
