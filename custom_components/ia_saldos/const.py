"""Constantes de la integración Saldos de IA y suscripciones."""

DOMAIN = "ia_saldos"

# servicio -> clave en el config entry
CLAVES = {
    "openrouter": "openrouter_key",
    "deepseek": "deepseek_key",
    "realdebrid": "realdebrid_key",
    "alldebrid": "alldebrid_key",
    "torbox": "torbox_key",
}

SERVICIOS_IA = ("openrouter", "deepseek")
SERVICIOS_DEBRID = ("realdebrid", "alldebrid", "torbox")

# minutos
INTERVALO_IA = 30
INTERVALO_DEBRID = 1440  # una vez al día: Real-Debrid penaliza el polling agresivo

TIMEOUT = 25

DISPOSITIVOS = {
    "openrouter": {
        "name": "OpenRouter",
        "manufacturer": "OpenRouter",
        "model": "Créditos de API",
        "url": "https://openrouter.ai/settings/credits",
    },
    "deepseek": {
        "name": "DeepSeek",
        "manufacturer": "DeepSeek",
        "model": "Plataforma",
        "url": "https://platform.deepseek.com/top_up",
    },
    "realdebrid": {
        "name": "Real-Debrid",
        "manufacturer": "Real-Debrid",
        "model": "Cuenta",
        "url": "https://real-debrid.com/account",
    },
    "alldebrid": {
        "name": "AllDebrid",
        "manufacturer": "AllDebrid",
        "model": "Cuenta",
        "url": "https://alldebrid.com/account/",
    },
    "torbox": {
        "name": "TorBox",
        "manufacturer": "TorBox",
        "model": "Cuenta",
        "url": "https://torbox.app/subscription",
    },
}

URL_OPENROUTER_CREDITOS = "https://openrouter.ai/api/v1/credits"
URL_OPENROUTER_CLAVE = "https://openrouter.ai/api/v1/key"
URL_DEEPSEEK_SALDO = "https://api.deepseek.com/user/balance"
URL_REALDEBRID_USER = "https://api.real-debrid.com/rest/1.0/user"
URL_ALDEBRID_USER = "https://api.alldebrid.com/v4/user?agent=hermes-ha"
URL_TORBOX_USER = "https://api.torbox.app/v1/api/user/me"
