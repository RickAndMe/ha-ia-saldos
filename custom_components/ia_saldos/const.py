"""Constantes de la integración Saldos de IA."""

DOMAIN = "ia_saldos"

CONF_OPENROUTER = "openrouter_key"
CONF_DEEPSEEK = "deepseek_key"
CONF_PINGEN_ID = "pingen_client_id"
CONF_PINGEN_SECRET = "pingen_client_secret"

OPENROUTER_SERVICIO = "openrouter"
DEEPSEEK_SERVICIO = "deepseek"
PINGEN_SERVICIO = "pingen"

UPDATE_INTERVAL = 30  # minutos

URL_OPENROUTER_CREDITOS = "https://openrouter.ai/api/v1/credits"
URL_OPENROUTER_CLAVE = "https://openrouter.ai/api/v1/key"
URL_DEEPSEEK_SALDO = "https://api.deepseek.com/user/balance"
URL_PINGEN_TOKEN = "https://api.pingen.com/auth/access-tokens"
URL_PINGEN_ORGANIZACIONES = "https://api.pingen.com/organisations"
PINGEN_SCOPE = "organisation_read"

TIMEOUT = 25

NOMBRES_DISPOSITIVO = {
    OPENROUTER_SERVICIO: {
        "name": "OpenRouter",
        "manufacturer": "OpenRouter",
        "model": "Créditos de API",
    },
    DEEPSEEK_SERVICIO: {
        "name": "DeepSeek",
        "manufacturer": "DeepSeek",
        "model": "Plataforma",
    },
    PINGEN_SERVICIO: {
        "name": "Pingen",
        "manufacturer": "Pingen",
        "model": "Saldo de envíos",
    },
}

URL_CUENTA = {
    OPENROUTER_SERVICIO: "https://openrouter.ai/settings/credits",
    DEEPSEEK_SERVICIO: "https://platform.deepseek.com/top_up",
    PINGEN_SERVICIO: "https://app.pingen.com",
}
