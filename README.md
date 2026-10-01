# MarkItDown Service

Contenedor Docker que expone [MarkItDown](https://github.com/microsoft/markitdown) de Microsoft con una página web sencilla: arrastras un archivo y obtienes su contenido en Markdown.

Formatos soportados: PDF, DOCX, XLSX, XLS, PPTX, HTML, CSV, JSON, XML, EPUB, imágenes, audio, ZIP, correo de Outlook y transcripciones de YouTube.

## Estructura

```
markitdown-service/
├── Dockerfile             imagen python:3.13-slim + ffmpeg + exiftool
├── docker-compose.yml     publica el puerto 8080 del host
├── requirements.txt
├── .dockerignore
└── app/
    ├── main.py            API FastAPI (/, /api/convert, /api/health)
    └── static/
        └── index.html     interfaz web (drag & drop, copiar, descargar .md)
```

## Uso

```bash
docker compose up -d --build
```

Abre <http://localhost:8080> y arrastra un archivo.

La interfaz es un banco de trabajo de dos paneles — **Origen** a la izquierda, **Markdown** a la derecha — que se apilan en pantallas estrechas:

| Panel | Botón | Qué hace |
|---|---|---|
| Origen | **De nuevo** | Vuelve a convertir el archivo ya cargado |
| Origen | **Quitar** | Descarta el archivo y devuelve la zona de arrastre |
| Markdown | **Copiar** | Copia el resultado al portapapeles |
| Markdown | **Descargar .md** | Guarda el resultado con el nombre del original |
| Markdown | **Limpiar** | Borra solo el resultado; el archivo sigue cargado |

Los botones se deshabilitan cuando no aplican. El pie de cada panel muestra los formatos admitidos y el recuento de caracteres, palabras y líneas. El botón **Tema** alterna claro/oscuro y recuerda la elección; por defecto sigue la preferencia del sistema.

Para detenerlo:

```bash
docker compose down
```

### Cambiar el puerto

Edita el mapeo en `docker-compose.yml` — el lado izquierdo es el puerto del host:

```yaml
ports:
  - "3000:8000"   # ahora responde en http://localhost:3000
```

Sin compose:

```bash
docker build -t markitdown-service .
docker run -d -p 8080:8000 --name markitdown markitdown-service
```

## API

Además de la interfaz web, el servicio expone:

- `POST /api/convert` — multipart con campo `file`; devuelve `{filename, markdown, chars}`
- `GET /api/health` — estado y límite de subida

```bash
curl -F "file=@documento.pdf" http://localhost:8080/api/convert
```

## Configuración

| Variable | Por defecto | Descripción |
|---|---|---|
| `MARKITDOWN_MAX_UPLOAD_MB` | `50` | Tamaño máximo de archivo aceptado |

## Alcance actual

- La conversión es **local y gratuita**, sin OCR. Funciona con PDFs de texto nativo; un PDF escaneado (imágenes puras) devolverá poco o ningún texto.
- Para escaneados, MarkItDown admite OCR vía LLM Vision (`enable_plugins=True` + cliente OpenAI) o Azure Document Intelligence. Ambos tienen costo por documento y requieren credenciales; no están cableados en esta versión.
- No hay autenticación ni rate limiting: pensado para uso en `localhost` o red interna. Añadir ambos antes de exponerlo públicamente.

## Nota sobre ejecución fuera del contenedor

En este equipo Windows, instalar el proyecto en un `venv` local falla al convertir PDF: App Control bloquea la DLL nativa `_cffi_backend`, lo que rompe la cadena `cryptography` → `pdfminer`. Dentro del contenedor (Linux) no ocurre. Usa Docker.
