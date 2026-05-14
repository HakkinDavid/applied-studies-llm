import re
from io import BytesIO
from typing import Any

from docx import Document
from fastapi import HTTPException
from pypdf import PdfReader

from app.core.config import MAX_REFERENCE_CHARS


def compact_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def make_excerpt(text: str, max_chars: int = MAX_REFERENCE_CHARS) -> str:
    clean = compact_spaces(text)

    if len(clean) <= max_chars:
        return clean

    return clean[:max_chars].rstrip() + "..."


def split_into_reference_chunks(text: str, prefix: str, page: int | None = None, max_chars: int = 1200) -> list[dict[str, Any]]:
    clean = compact_spaces(text)

    if not clean:
        return []

    chunks = []
    start = 0
    counter = 1

    while start < len(clean):
        end = min(start + max_chars, len(clean))
        piece = clean[start:end].strip()

        if piece:
            ref_id = f"{prefix}-{counter}"
            chunks.append(
                {
                    "ref_id": ref_id,
                    "page": page,
                    "excerpt": make_excerpt(piece),
                    "text": piece,
                }
            )

        start = end
        counter += 1

    return chunks


def extract_pdf_text_and_references(data: bytes) -> tuple[str, list[dict[str, Any]]]:
    try:
        reader = PdfReader(BytesIO(data))
        pages = []
        references = []

        for index, page in enumerate(reader.pages, start=1):
            page_text = page.extract_text() or ""
            pages.append(page_text)
            references.extend(
                split_into_reference_chunks(
                    text=page_text,
                    prefix=f"p{index}",
                    page=index,
                )
            )

        return "\n".join(pages), references
    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail=f"No se pudo leer el PDF: {error}",
        )


def extract_docx_text_and_references(data: bytes) -> tuple[str, list[dict[str, Any]]]:
    try:
        document = Document(BytesIO(data))
        paragraphs = [paragraph.text for paragraph in document.paragraphs if paragraph.text.strip()]
        full_text = "\n".join(paragraphs)
        references = []

        for index, paragraph in enumerate(paragraphs, start=1):
            references.extend(
                split_into_reference_chunks(
                    text=paragraph,
                    prefix=f"par{index}",
                    page=None,
                )
            )

        if not references and full_text:
            references = split_into_reference_chunks(full_text, prefix="doc", page=None)

        return full_text, references
    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail=f"No se pudo leer el DOCX: {error}",
        )


def extract_plain_text_and_references(data: bytes) -> tuple[str, list[dict[str, Any]]]:
    text = None

    for encoding in ["utf-8", "latin-1"]:
        try:
            text = data.decode(encoding)
            break
        except UnicodeDecodeError:
            pass

    if text is None:
        raise HTTPException(
            status_code=400,
            detail="No se pudo leer el archivo de texto.",
        )

    references = split_into_reference_chunks(text, prefix="txt", page=None)
    return text, references


def extract_text_and_references(data: bytes, extension: str) -> tuple[str, list[dict[str, Any]]]:
    if extension == ".pdf":
        return extract_pdf_text_and_references(data)

    if extension == ".docx":
        return extract_docx_text_and_references(data)

    if extension in [".txt", ".md"]:
        return extract_plain_text_and_references(data)

    raise HTTPException(
        status_code=400,
        detail="No hay extractor disponible para este formato.",
    )


def clean_text(text: str) -> str:
    lines = []

    for line in text.splitlines():
        clean_line = line.strip()
        if clean_line:
            lines.append(clean_line)

    return "\n".join(lines)


def clean_references(references: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cleaned = []

    for item in references:
        text = compact_spaces(str(item.get("text", "")))
        excerpt = make_excerpt(text)

        if not text:
            continue

        cleaned.append(
            {
                "ref_id": str(item.get("ref_id")),
                "page": item.get("page"),
                "excerpt": excerpt,
                "text": text,
            }
        )

    return cleaned


def limit_text_for_generation(text: str, max_chars: int = 25000) -> str:
    if len(text) <= max_chars:
        return text

    start = text[: max_chars // 2]
    end = text[-max_chars // 2:]

    return start + "\n\n[...contenido omitido por longitud...]\n\n" + end


def references_for_prompt(references: list[dict[str, Any]], max_items: int) -> str:
    selected = references[:max_items]
    lines = []

    for ref in selected:
        page = ref.get("page")
        page_text = f"página {page}" if page else "sin página"
        lines.append(f"[{ref['ref_id']}] ({page_text}) {ref['excerpt']}")

    return "\n".join(lines)
