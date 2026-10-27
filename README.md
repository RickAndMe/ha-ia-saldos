# Saldos para Home Assistant

Integración personalizada para Home Assistant que muestra, como sensores nativos, el
crédito disponible en **OpenRouter**, el saldo de **DeepSeek** y el saldo de envíos de
**Pingen**.

Sin dependencias externas, sin scripts y sin nada corriendo fuera de Home Assistant:
la consulta la hace la propia integración cada 30 minutos.

## Instalación

1. HACS → Integraciones → menú → **Repositorios personalizados**.
2. Añade `https://github.com/RickAndMe/ha-ia-saldos` con categoría **Integration**.
3. Instálala y reinicia Home Assistant.
4. Ajustes → Dispositivos y servicios → **Añadir integración** → «Saldos».
5. Pega las claves que tengas. Las que no uses, déjalas en blanco.

Para añadir o cambiar una clave más tarde: en la integración, botón **Configurar**.
Lo que dejes en blanco no se toca, así que puedes añadir Pingen sin volver a escribir
las claves de IA.

## Sensores

Todos se consultan cada **30 minutos**. Cada servicio es un dispositivo, con sus
sensores dentro.

**OpenRouter**

| Sensor | Qué es |
|---|---|
| Crédito de la clave | Lo que te queda gastable según el límite de la clave. **Es el que te limita de verdad.** |
| Saldo de la cuenta | Créditos comprados menos gasto acumulado. |
| Límite de la clave | Tope configurado en esa clave. |
| Gastado hoy / este mes / histórico | Consumo por periodo. |
| Créditos comprados | Total recargado histórico. |

**DeepSeek**: saldo, saldo recargado y saldo de regalo.

**Pingen**

| Sensor | Qué es |
|---|---|
| Saldo | `billing_balance` de la organización, con la moneda que devuelve la API (CHF) |
| Créditos que faltan | Lo que te falta para cubrir el envío pendiente |
| Plan | El plan contratado |

El sensor de saldo lleva como atributos la organización, su estado y el modo de
facturación.

## Cómo sacar las credenciales de Pingen

Pingen no usa una clave simple, sino OAuth2 con *client credentials*:

1. Entra en https://app.pingen.com → **Settings → API**.
2. Crea una aplicación y copia el **client_id** y el **client_secret**.
3. Dale el permiso `organisation_read`, que es el único que hace falta para leer el saldo.

Pega los dos en la integración. Si falta uno de los dos, el alta se rechaza con un aviso
claro en vez de guardar algo incompleto.

## Aviso antes de quedarte sin saldo

```yaml
trigger:
  - platform: numeric_state
    entity_id: sensor.openrouter_credito_de_la_clave
    below: 2
action:
  - service: notify.send_message
    target:
      entity_id: notify.iphone
    data:
      message: "Quedan {{ states('sensor.openrouter_credito_de_la_clave') }} $ de crédito"
```

## Detalles

- **Cada 30 minutos**, con reintento automático.
- Si una API falla, los sensores de los demás servicios **siguen funcionando**; solo los
  del servicio caído pasan a `unavailable`.
- La clave se rechaza en el alta si la API no responde correctamente, así que no se
  guarda una clave mal escrita.
- Todo se configura desde la interfaz.

## APIs utilizadas

- OpenRouter: `GET /api/v1/credits` y `GET /api/v1/key`
- DeepSeek: `GET /user/balance`
- Pingen: `POST /auth/access-tokens` (OAuth2 client_credentials) y `GET /organisations`

## Licencia

MIT
