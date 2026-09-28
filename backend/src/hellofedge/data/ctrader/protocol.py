"""Messages de l'API cTrader (Spotware) en JSON, et la liste blanche de ceux qu'on envoie.

Chaque message est `{"clientMsgId": ..., "payloadType": <entier>, "payload": {...}}`.
Les numéros viennent des définitions officielles (`openapi-proto-messages` de Spotware).

Lecture seule (AC-14) : le client refuse d'envoyer un message absent de `SENDABLE`.
Aucun message d'ordre, de position ou de compte en écriture n'y figure.
"""

from enum import IntEnum


class Msg(IntEnum):
    # Messages communs
    ERROR_RES = 50
    HEARTBEAT_EVENT = 51

    # Messages Open API
    APPLICATION_AUTH_REQ = 2100
    APPLICATION_AUTH_RES = 2101
    ACCOUNT_AUTH_REQ = 2102
    ACCOUNT_AUTH_RES = 2103
    VERSION_REQ = 2104
    VERSION_RES = 2105
    SYMBOLS_LIST_REQ = 2114
    SYMBOLS_LIST_RES = 2115
    SYMBOL_BY_ID_REQ = 2116
    SYMBOL_BY_ID_RES = 2117
    GET_TRENDBARS_REQ = 2137
    GET_TRENDBARS_RES = 2138
    OA_ERROR_RES = 2142
    ACCOUNTS_TOKEN_INVALIDATED_EVENT = 2147
    CLIENT_DISCONNECT_EVENT = 2148
    GET_ACCOUNTS_BY_ACCESS_TOKEN_REQ = 2149
    GET_ACCOUNTS_BY_ACCESS_TOKEN_RES = 2150
    ACCOUNT_DISCONNECT_EVENT = 2164
    REFRESH_TOKEN_REQ = 2173
    REFRESH_TOKEN_RES = 2174


# La liste blanche : les seuls messages que le client a le droit d'envoyer.
SENDABLE: frozenset[int] = frozenset(
    {
        Msg.HEARTBEAT_EVENT,
        Msg.APPLICATION_AUTH_REQ,
        Msg.ACCOUNT_AUTH_REQ,
        Msg.VERSION_REQ,
        Msg.SYMBOLS_LIST_REQ,
        Msg.SYMBOL_BY_ID_REQ,
        Msg.GET_TRENDBARS_REQ,
        Msg.GET_ACCOUNTS_BY_ACCESS_TOKEN_REQ,
        Msg.REFRESH_TOKEN_REQ,
    }
)

# Réponse attendue pour chaque requête envoyée.
RESPONSE_OF: dict[int, int] = {
    Msg.APPLICATION_AUTH_REQ: Msg.APPLICATION_AUTH_RES,
    Msg.ACCOUNT_AUTH_REQ: Msg.ACCOUNT_AUTH_RES,
    Msg.VERSION_REQ: Msg.VERSION_RES,
    Msg.SYMBOLS_LIST_REQ: Msg.SYMBOLS_LIST_RES,
    Msg.SYMBOL_BY_ID_REQ: Msg.SYMBOL_BY_ID_RES,
    Msg.GET_TRENDBARS_REQ: Msg.GET_TRENDBARS_RES,
    Msg.GET_ACCOUNTS_BY_ACCESS_TOKEN_REQ: Msg.GET_ACCOUNTS_BY_ACCESS_TOKEN_RES,
    Msg.REFRESH_TOKEN_REQ: Msg.REFRESH_TOKEN_RES,
}

# Période M1 des bougies (énumération ProtoOATrendbarPeriod).
PERIOD_M1 = 1

# Au plus 14 000 bougies par requête : au delà, cTrader tronque sans erreur.
MAX_BARS_PER_REQUEST = 14_000

# Les prix des bougies arrivent en entiers, en 1/100 000.
PRICE_SCALE = 100_000

# Codes d'erreur (ProtoOAErrorCode) qui veulent dire « jeton, compte ou application refusés ».
AUTH_ERROR_CODES = frozenset(
    {
        "OA_AUTH_TOKEN_EXPIRED",
        "ACCOUNT_NOT_AUTHORIZED",
        "RET_NO_SUCH_LOGIN",
        "RET_ACCOUNT_DISABLED",
        "CH_CLIENT_AUTH_FAILURE",
        "CH_CLIENT_NOT_AUTHENTICATED",
        "CH_ACCESS_TOKEN_INVALID",
        "CH_CTID_TRADER_ACCOUNT_NOT_FOUND",
    }
)

# Codes d'erreur qui veulent dire « trop de requêtes, attendre ».
RATE_LIMIT_ERROR_CODES = frozenset(
    {"REQUEST_FREQUENCY_EXCEEDED", "BLOCKED_PAYLOAD_TYPE"}
)

# Le compte est déjà authentifié sur cette connexion : ce n'est pas une panne.
ALREADY_LOGGED_IN = "ALREADY_LOGGED_IN"


def host_for(env: str) -> str:
    """Adresse du serveur cTrader en JSON sur WebSocket (port 5036)."""
    if env not in ("demo", "live"):
        raise ValueError(f"CTRADER_ENV doit valoir demo ou live, reçu {env!r}")
    return f"wss://{env}.ctraderapi.com:5036"
