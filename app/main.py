import logging
import os
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from markitdown import MarkItDown

STATIC_DIR = Path(__file__).parent / "static"

MAX_UPLOAD_MB = int(os.getenv("MARKITDOWN_MAX_UPLOAD_MB", "50"))
MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024

app = FastAPI(title="MarkItDown Service", version="2.0")

logger = logging.getLogger("markitdown-service")

_converter = MarkItDown(enable_plugins=False)


def explain(exc: Exception) -> str:
    """Traduce el fallo tecnico a algo accionable para quien sube el archivo.

    El detalle tecnico se queda en el log del contenedor, no en la interfaz.
    """
    text = str(exc).lower()
    if "missingdependency" in text or "have not been installed" in text:
        return "Este formato no esta habilitado en esta version del servicio."
    if "password" in text or "encrypted" in text:
        return "El archivo esta protegido con contrasena. Quita la proteccion y vuelve a intentarlo."
    if "syntaxerror" in text or "is this really" in text or "not a" in text:
        return "El archivo parece danado o su contenido no coincide con su extension."
    return (
        "No se pudo leer el archivo. Puede estar danado, protegido "
        "o en un formato que el servicio no soporta."
    )


@app.get("/api/health")
def health():
    return {"status": "ok", "max_upload_mb": MAX_UPLOAD_MB}


@app.post("/api/convert")
async def convert(file: UploadFile = File(...)):
    filename = file.filename or ""
    suffix = Path(filename).suffix
    if not suffix:
        raise HTTPException(status_code=400, detail="El archivo debe tener extension (.pdf, .docx, ...)")

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="El archivo esta vacio")
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail=f"Archivo demasiado grande (max {MAX_UPLOAD_MB} MB)")

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(data)
        tmp_path = tmp.name

    try:
        result = _converter.convert(tmp_path)
    except Exception as exc:
        logger.exception("Fallo la conversion de %s", filename)
        raise HTTPException(status_code=422, detail=explain(exc)) from exc
    finally:
        os.unlink(tmp_path)

    return {
        "filename": filename,
        "markdown": result.text_content,
        "chars": len(result.text_content),
    }


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
