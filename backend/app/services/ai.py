from typing import Any

from fastapi import HTTPException
from openai import OpenAI

from app.core.config import MODEL, OPENAI_API_KEY, OPENAI_BASE_URL
from app.services.utils import extract_json_from_model_text


client = OpenAI(
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_BASE_URL,
) if OPENAI_API_KEY and OPENAI_BASE_URL and MODEL else None


def is_ai_configured() -> bool:
    return client is not None


def ensure_ai_client() -> None:
    if not OPENAI_BASE_URL:
        raise HTTPException(
            status_code=500,
            detail="Falta configurar OPENAI_BASE_URL en el archivo .env.",
        )

    if not OPENAI_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="Falta configurar OPENAI_API_KEY en el archivo .env.",
        )

    if not MODEL:
        raise HTTPException(
            status_code=500,
            detail="Falta configurar MODEL en el archivo .env.",
        )

    if client is None:
        raise HTTPException(
            status_code=500,
            detail="No se pudo inicializar el cliente de IA.",
        )


def model_error_mentions_temperature(error: Exception) -> bool:
    message = str(error).lower()

    return (
        "temperature" in message
        and (
            "unsupported" in message
            or "does not support" in message
            or "unsupported value" in message
        )
    )


def create_chat_completion_without_temperature(
    system_message: str,
    user_message: str,
):
    return client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": system_message,
            },
            {
                "role": "user",
                "content": user_message,
            },
        ],
    )


def create_chat_completion_with_temperature(
    system_message: str,
    user_message: str,
    temperature: float,
):
    return client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": system_message,
            },
            {
                "role": "user",
                "content": user_message,
            },
        ],
        temperature=temperature,
    )


def call_ai_text(system_message: str, user_message: str, temperature: float | None = None) -> str:
    ensure_ai_client()

    try:
        if temperature is None:
            response = create_chat_completion_without_temperature(
                system_message=system_message,
                user_message=user_message,
            )
        else:
            response = create_chat_completion_with_temperature(
                system_message=system_message,
                user_message=user_message,
                temperature=temperature,
            )

    except Exception as error:
        if temperature is not None and model_error_mentions_temperature(error):
            try:
                response = create_chat_completion_without_temperature(
                    system_message=system_message,
                    user_message=user_message,
                )
            except Exception as retry_error:
                raise HTTPException(
                    status_code=500,
                    detail=f"Error al comunicarse con el servicio de IA usando la librería de OpenAI: {retry_error}",
                )

        else:
            raise HTTPException(
                status_code=500,
                detail=f"Error al comunicarse con el servicio de IA usando la librería de OpenAI: {error}",
            )

    content = response.choices[0].message.content

    if not content:
        raise HTTPException(
            status_code=500,
            detail="El modelo respondió vacío.",
        )

    return content


def call_ai_json(system_message: str, user_message: str, temperature: float | None = None) -> Any:
    content = call_ai_text(
        system_message=system_message,
        user_message=user_message,
        temperature=temperature,
    )

    return extract_json_from_model_text(content)