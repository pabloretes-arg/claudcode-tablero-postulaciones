"""Tablero de postulaciones laborales (Streamlit).

Lee el Registro de postulaciones desde Google Docs (solo lectura); si no hay
conexión usa el último texto descargado o, en su defecto, el .txt local.
Guarda estado y fecha de último contacto en "estados_postulaciones.json".
"""
import json
from datetime import date, datetime
from pathlib import Path

import pandas as pd
import streamlit as st

from google_docs import leer_documento

CARPETA = Path(__file__).resolve().parent
ARCHIVO_TXT = CARPETA / "Registro de postulaciones.txt"
ARCHIVO_ESTADOS = CARPETA / "estados_postulaciones.json"
ARCHIVO_RESPALDO = CARPETA / "ultimo_registro_google_docs.txt"

ESTADOS = ["Esperando", "Respondieron", "Entrevista", "Descartado", "Rechazado"]
ESTADO_INICIAL = "Esperando"
DIAS_SEGUIMIENTO = 7
CAMPOS = ["Fecha", "Empresa", "Rol", "Carril", "Canal", "Publicado hace", "Salario", "Link CV"]
CAMPO_OPCIONAL = "Postulantes"  # 9.º campo, opcional
SIN_DATO = "—"


@st.cache_data(ttl=60, show_spinner="Leyendo Google Docs…")
def _descargar() -> str:
    texto = leer_documento()
    ARCHIVO_RESPALDO.write_text(texto, encoding="utf-8")
    return texto


def obtener_texto():
    """Devuelve (texto, aviso). aviso es None si se leyó de Google Docs."""
    try:
        return _descargar(), None
    except Exception as e:  # sin conexión, sin token, permisos, etc.
        motivo = f"{type(e).__name__}: {e}"
    for archivo, nombre in ((ARCHIVO_RESPALDO, "la última copia descargada de Google Docs"),
                            (ARCHIVO_TXT, "el .txt local")):
        if archivo.exists():
            return (archivo.read_text(encoding="utf-8-sig"),
                    f"⚠️ No pude leer Google Docs, uso {nombre}. Los datos pueden estar desactualizados. ({motivo})")
    return "", f"⚠️ No pude leer Google Docs y no hay respaldo. ({motivo})"


def parsear(texto: str) -> pd.DataFrame:
    """Devuelve solo las líneas con el formato esperado."""
    filas = []
    for linea in texto.lstrip("\ufeff").splitlines():
        partes = [p.strip() for p in linea.split("|")]
        if len(partes) == len(CAMPOS):
            partes.append("")
        if len(partes) != len(CAMPOS) + 1:
            continue
        try:
            fecha = datetime.strptime(partes[0], "%d/%m/%Y").date()
        except ValueError:
            continue
        fila = dict(zip(CAMPOS + [CAMPO_OPCIONAL], partes))
        fila["Fecha"] = fecha
        fila[CAMPO_OPCIONAL] = fila[CAMPO_OPCIONAL] or SIN_DATO
        filas.append(fila)
    df = pd.DataFrame(filas, columns=CAMPOS + [CAMPO_OPCIONAL])
    df["id"] = df["Fecha"].astype(str) + "|" + df["Empresa"] + "|" + df["Rol"]
    return df


def cargar_estados() -> dict:
    if ARCHIVO_ESTADOS.exists():
        try:
            return json.loads(ARCHIVO_ESTADOS.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            st.warning("No pude leer el archivo de estados; empiezo con uno vacío.")
    return {}


def guardar_estados(estados: dict) -> None:
    tmp = ARCHIVO_ESTADOS.with_suffix(".tmp")
    tmp.write_text(json.dumps(estados, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(ARCHIVO_ESTADOS)


def conteo(serie: pd.Series, nombre: str) -> pd.DataFrame:
    return serie.value_counts().rename_axis(nombre).reset_index(name="Postulaciones")


def construir_tabla(df: pd.DataFrame, estados: dict) -> pd.DataFrame:
    t = df.copy()
    t["Estado"] = t["id"].map(lambda i: estados.get(i, {}).get("estado", ESTADO_INICIAL))

    def contacto(i):
        valor = estados.get(i, {}).get("ultimo_contacto")
        return date.fromisoformat(valor) if valor else None

    t["Último contacto"] = t["id"].map(contacto)
    return t


st.set_page_config(page_title="Tablero de postulaciones", page_icon="📋", layout="wide")
st.title("📋 Tablero de postulaciones")

texto, aviso = obtener_texto()
if aviso:
    st.warning(aviso)
else:
    st.caption("🟢 Datos leídos en vivo desde Google Docs (se actualizan cada 60 s).")
if st.button("🔄 Releer Google Docs"):
    _descargar.clear()
    st.rerun()

df = parsear(texto)
if df.empty:
    st.info("No encontré postulaciones válidas en el registro.")
    st.stop()

estados = cargar_estados()

# ---------- Resumen ----------
st.header("Resumen")
st.metric("Total de postulaciones", len(df))
c1, c2 = st.columns(2)
with c1:
    st.subheader("Por carril")
    por_carril = conteo(df["Carril"], "Carril")
    st.bar_chart(por_carril, x="Carril", y="Postulaciones", horizontal=True)
with c2:
    st.subheader("Por canal")
    por_canal = conteo(df["Canal"], "Canal")
    st.bar_chart(por_canal, x="Canal", y="Postulaciones", horizontal=True)

# ---------- Tabla editable ----------
st.header("Todas las postulaciones")
st.caption("Editá el estado y la fecha de último contacto, y después tocá «Guardar cambios».")

tabla = construir_tabla(df, estados)
columnas = ["Fecha", "Empresa", "Rol", "Carril", "Canal", "Publicado hace", "Salario", "Postulantes",
            "Estado", "Último contacto", "Link CV"]
editada = st.data_editor(
    tabla[columnas],
    hide_index=True,
    width="stretch",
    disabled=[c for c in columnas if c not in ("Estado", "Último contacto")],
    column_config={
        "Fecha": st.column_config.DateColumn("Fecha", format="DD/MM/YYYY"),
        "Estado": st.column_config.SelectboxColumn("Estado", options=ESTADOS, required=True),
        "Último contacto": st.column_config.DateColumn("Último contacto", format="DD/MM/YYYY"),
        "Link CV": st.column_config.LinkColumn("Link CV", display_text="Abrir CV"),
    },
    key="editor",
)

if st.button("💾 Guardar cambios", type="primary"):
    nuevos = {}
    for i, fila in zip(tabla["id"], editada.itertuples(index=False)):
        contacto = fila[columnas.index("Último contacto")]
        estado = fila[columnas.index("Estado")]
        nuevos[i] = {
            "estado": estado if estado in ESTADOS else ESTADO_INICIAL,
            "ultimo_contacto": None if pd.isna(contacto) else pd.Timestamp(contacto).date().isoformat(),
        }
    guardar_estados(nuevos)
    st.success("Cambios guardados.")
    estados = nuevos

# ---------- Toca seguimiento ----------
st.header("🔔 Toca seguimiento")
st.caption(
    f"Estado Esperando o Entrevista, con más de {DIAS_SEGUIMIENTO} días sin contacto "
    "(desde el último contacto o, si no hay, desde la postulación)."
)

seg = construir_tabla(df, estados)
hoy = date.today()
seg["Referencia"] = seg.apply(
    lambda f: f["Último contacto"] if f["Último contacto"] is not None else f["Fecha"], axis=1
)
seg["Días sin contacto"] = seg["Referencia"].map(lambda d: (hoy - d).days)
seg = seg[seg["Estado"].isin(["Esperando", "Entrevista"]) & (seg["Días sin contacto"] > DIAS_SEGUIMIENTO)]
seg = seg.sort_values("Referencia")  # de la más vieja a la más nueva

if seg.empty:
    st.success("Nada pendiente de seguimiento. 🎉")
else:
    st.dataframe(
        seg[["Empresa", "Rol", "Estado", "Postulantes", "Fecha", "Último contacto", "Días sin contacto", "Link CV"]],
        hide_index=True,
        width="stretch",
        column_config={
            "Fecha": st.column_config.DateColumn("Postulada el", format="DD/MM/YYYY"),
            "Último contacto": st.column_config.DateColumn("Último contacto", format="DD/MM/YYYY"),
            "Link CV": st.column_config.LinkColumn("Link CV", display_text="Abrir CV"),
        },
    )
