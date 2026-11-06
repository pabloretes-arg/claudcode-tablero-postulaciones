"""Autorización única con Google (permiso de solo lectura). Crea token.json."""
from google_auth_oauthlib.flow import InstalledAppFlow

from google_docs import ARCHIVO_CREDENCIALES, ARCHIVO_TOKEN, SCOPES

if not ARCHIVO_CREDENCIALES.exists():
    raise SystemExit(f"No encuentro {ARCHIVO_CREDENCIALES.name} en esta carpeta. Seguí la guía de Google Cloud.")

flujo = InstalledAppFlow.from_client_secrets_file(str(ARCHIVO_CREDENCIALES), SCOPES)
creds = flujo.run_local_server(port=0)  # abre el navegador
ARCHIVO_TOKEN.write_text(creds.to_json(), encoding="utf-8")
print(f"Listo. Se guardó {ARCHIVO_TOKEN.name}. Ya podés abrir el tablero.")
