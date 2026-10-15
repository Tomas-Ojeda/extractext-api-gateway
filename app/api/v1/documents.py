import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel

from app.api.dependencies import get_http_client
from config.settings import settings

router = APIRouter(prefix="/documents", tags=["documents"])


class DocumentResponse(BaseModel):
    id: str
    filename: str
    content: str
    checksum: str


class DocumentSummaryResponse(BaseModel):
    id: str
    filename: str
    checksum: str


class UpdateDocumentRequest(BaseModel):
    content: str


def _extract_detail(response: httpx.Response, default: str) -> str:
    try:
        payload = response.json()
    except ValueError:
        return default
    if isinstance(payload, dict) and "detail" in payload:
        return str(payload["detail"])
    return default


def _propagate_http_error(response: httpx.Response, default: str) -> None:
    if 400 <= response.status_code < 500:
        raise HTTPException(
            status_code=response.status_code,
            detail=_extract_detail(response, default),
        )
    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail=f"{default}: {response.text}",
    )


@router.get("/", response_model=list[DocumentSummaryResponse])
async def list_documents(
    request: Request,
    client: httpx.AsyncClient = Depends(get_http_client),
):
    url = f"{settings.storage_url}/api/v1/documents/"
    try:
        response = await client.get(
            url, params=dict(request.query_params), timeout=settings.storage_timeout_seconds
        )
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Error al listar documentos: {str(exc)}",
        )
    if response.status_code >= 400:
        _propagate_http_error(response, "Error al listar documentos")
    return Response(
        content=response.content,
        status_code=response.status_code,
        media_type="application/json",
    )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    client: httpx.AsyncClient = Depends(get_http_client),
):
    url = f"{settings.storage_url}/api/v1/documents/{document_id}"
    try:
        response = await client.get(url, timeout=settings.storage_timeout_seconds)
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Error al obtener documento: {str(exc)}",
        )
    if response.status_code >= 400:
        _propagate_http_error(response, "Error al obtener documento")
    return Response(
        content=response.content,
        status_code=response.status_code,
        media_type="application/json",
    )


@router.post(
    "/",
    response_model=DocumentResponse,
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {
                "multipart/form-data": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "file": {"type": "string", "format": "binary"}
                        },
                        "required": ["file"],
                    }
                }
            },
        }
    },
)
async def upload_document(
    request: Request,
    client: httpx.AsyncClient = Depends(get_http_client),
):
    content_type = request.headers.get("content-type")
    if not content_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Falta el Content-Type de la carga",
        )

    content_length = request.headers.get("content-length")
    if content_length is not None:
        try:
            declared_size = int(content_length)
        except ValueError:
            declared_size = None
        if declared_size is not None:
            max_allowed = settings.pdf_max_size_bytes + 64 * 1024
            if declared_size > max_allowed:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail="El archivo supera el tamano maximo permitido",
                )

    url = f"{settings.ingestion_url}/api/v1/documents/"
    try:
        response = await client.post(
            url,
            content=request.stream(),
            headers={"content-type": content_type},
            timeout=settings.ingestion_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Error al subir documento: {str(exc)}",
        )

    if 200 <= response.status_code < 300:
        return Response(
            content=response.content,
            status_code=response.status_code,
            media_type="application/json",
        )

    if 400 <= response.status_code < 500:
        raise HTTPException(
            status_code=response.status_code,
            detail=_extract_detail(response, "Error al procesar el documento"),
        )

    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail=f"Error al subir documento: {response.text}",
    )


@router.put("/{document_id}", response_model=DocumentResponse)
async def update_document(document_id: str, body: UpdateDocumentRequest, client: httpx.AsyncClient = Depends(get_http_client)):
    """Actualiza el contenido de un documento en el microservicio storage."""
    url = f"{settings.storage_url}/api/v1/documents/{document_id}"
    try:
        response = await client.put(
            url,
            json={"content": body.content},
            timeout=settings.storage_timeout_seconds,
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Documento no encontrado",
            )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Error al actualizar documento: {str(e)}",
        )
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Error al actualizar documento: {str(e)}",
        )

    return response.json()


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(document_id: str, client: httpx.AsyncClient = Depends(get_http_client)):
    """Elimina un documento por su id desde el microservicio storage."""
    url = f"{settings.storage_url}/api/v1/documents/{document_id}"
    try:
        response = await client.delete(url, timeout=settings.storage_timeout_seconds)
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Documento no encontrado",
            )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Error al eliminar documento: {str(e)}",
        )
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Error al eliminar documento: {str(e)}",
        )