# Tablero de postulaciones

Tablero en Streamlit para seguir postulaciones laborales. Lee un registro desde
Google Docs (solo lectura) y permite marcar estado y fecha de último contacto.

## Formato del registro

Una línea por postulación:

```
Fecha | Empresa | Rol | Carril | Canal | Publicado hace | Salario | Link CV
06/11/2026 | Empresa SA | Rol | Sales | Portal | 2 h | 5.000 | https://...
```

Las líneas que no tengan ese formato se ignoran.

## Instalación

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Conexión con Google Docs (OAuth, solo lectura)

1. En Google Cloud: crear un proyecto, habilitar **Google Docs API**, configurar la
   pantalla de consentimiento (usuario de prueba: tu mail) con el permiso
   `https://www.googleapis.com/auth/documents.readonly`.
2. Crear un cliente OAuth de tipo **App de escritorio**, descargar el JSON y
   guardarlo como `credentials.json` en esta carpeta.
3. Crear `documento_id.txt` con el ID del Doc (o definir la variable `DOCUMENTO_ID`).
4. Autorizar una vez: `.venv/bin/python autorizar.py` (crea `token.json`).

`credentials.json`, `token.json`, `documento_id.txt` y tus datos están en `.gitignore`.

## Uso

```bash
.venv/bin/streamlit run app.py
```

Sin conexión o sin token, usa la última copia descargada (o un
`Registro de postulaciones.txt` local) y lo avisa en pantalla.
El estado de cada postulación se guarda en `estados_postulaciones.json`.
