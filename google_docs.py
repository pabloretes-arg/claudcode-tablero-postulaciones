"""Lectura del Registro de postulaciones desde Google Docs (solo lectura)."""
import os
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

CARPETA = Path(__file__).resolve().parent
ARCHIVO_CREDENCIALES = CARPETA / "credentials.json"  # lo descargás de Google Cloud
ARCHIVO_TOKEN = CARPETA / "token.json"  # lo crea autorizar.py
SCOPES = ["https://www.googleapis.com/auth/documents.readonly"]
ARCHIVO_DOCUMENTO_ID = CARPETA / "documento_id.txt"  # una línea con el ID del Doc


def _documento_id() -> str:
    """ID del documento: variable de entorno DOCUMENTO_ID o archivo documento_id.txt."""
    valor = os.environ.get("DOCUMENTO_ID", "").strip()
    if not valor and ARCHIVO_DOCUMENTO_ID.exists():
        valor = ARCHIVO_DOCUMENTO_ID.read_text(encoding="utf-8").strip()
    if not valor:
        raise RuntimeError("Falta el ID del documento: creá documento_id.txt (ver README).")
    return valor


def _extraer_texto(doc: dict) -> str:
    """Devuelve el texto del documento, un párrafo por línea."""
    lineas = []
    for elemento in doc.get("body", {}).get("content", []):
        parrafo = elemento.get("paragraph")
        if not parrafo:
            continue
        texto = "".join(
            e.get("textRun", {}).get("content", "") for e in parrafo.get("elements", [])
        )
        lineas.append(texto.rstrip("\n").replace("\x0b", " "))  # \x0b = salto suave
    return "\n".join(lineas)


def leer_documento() -> str:
    """Lee el documento. Lanza una excepción si no hay token o no hay conexión."""
    if not ARCHIVO_TOKEN.exists():
        raise RuntimeError("Falta autorizar: corré «python autorizar.py» una vez.")
    creds = Credentials.from_authorized_user_file(str(ARCHIVO_TOKEN), SCOPES)
    if not creds.valid:
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            ARCHIVO_TOKEN.write_text(creds.to_json(), encoding="utf-8")
        else:
            raise RuntimeError("El token venció: corré «python autorizar.py» de nuevo.")
    servicio = build("docs", "v1", credentials=creds, cache_discovery=False)
    doc = servicio.documents().get(documentId=_documento_id()).execute()
    return _extraer_texto(doc)
