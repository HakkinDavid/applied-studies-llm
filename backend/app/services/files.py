import hashlib
from pathlib import Path

from fastapi import HTTPException

from app.core.config import ALLOWED_EXTENSIONS, MAX_FILE_SIZE_BYTES, MAX_FILE_SIZE_MB


def calculate_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def get_extension(filename: str) -> str:
    return Path(filename).suffix.lower()


def validate_file(filename: str, data: bytes) -> str:
    extension = get_extension(filename)

    if extension not in ALLOWED_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_EXTENSIONS))
        raise HTTPException(
            status_code=400,
            detail=f"Formato no soportado. Formatos permitidos: {allowed}",
        )

    if len(data) == 0:
        raise HTTPException(
            status_code=400,
            detail="El archivo está vacío.",
        )

    if len(data) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"El archivo supera el límite de {MAX_FILE_SIZE_MB} MB.",
        )

    return extension
