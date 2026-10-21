"""Comprueba ping por HTTPS sin cuenta, secretos ni cambios de datos."""

import json
from pathlib import Path
from urllib.request import Request, urlopen


def main() -> None:
    configuracion = json.loads(Path("config/pea.config.json").read_text(encoding="utf-8"))
    url = configuracion["url"]
    clave = configuracion["clave_publishable"]
    if url != "https://wdmchsncexayqbjueamb.supabase.co" or not clave.startswith("sb_publishable_"):
        raise ValueError("La configuracion publica no corresponde a pea-prod.")
    solicitud = Request(url + "/rest/v1/rpc/ping", data=b"{}", headers={
        "apikey": clave, "Content-Type": "application/json",
        "User-Agent": "PEA-i/1.0 (Universidad Popular del Cesar; comprobacion de disponibilidad)",
    }, method="POST")
    with urlopen(solicitud, timeout=25) as respuesta:
        estado = json.load(respuesta)
    if not isinstance(estado, dict) or estado.get("estado") != "ok":
        raise RuntimeError("Supabase no confirmo disponibilidad.")
    print("pea-prod responde correctamente por HTTPS.")


if __name__ == "__main__":
    main()
