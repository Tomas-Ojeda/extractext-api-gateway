import httpx
from fastapi import APIRouter, HTTPException, Response, UploadFile, File, status
from pydantic import BaseModel

from config.settings import settings

router = APIRouter(prefix="/documents", tags=["documents"])


class DocumentResponse(BaseModel):
    id: str
    filename: str
    content: str
    checksum: str


class UpdateDocumentRequest(BaseModel):
    content: str


@router.post("/", response_model=DocumentResponse)
async def upload_document(file: UploadFile = File(...), response: Response = None):
    """Recibe un PDF y lo reenvia al servicio de ingestion."""
    file_bytes = await file.read()
    url = f"{settings.ingestion_url}/api/v1/documents/"
    try:
        async with httpx.AsyncClient() as client:
            http_response = await client.post(
                url,
                files={"file": (file.filename or "", file_bytes, "application/pdf")},
                timeout=45.0,
            )
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Error al subir documento: {str(exc)}",
        )

    if 200 <= http_response.status_code < 300:
        try:
            data = http_response.json()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Respuesta invalida del servicio de ingestion",
            )
        response.status_code = http_response.status_code
        return DocumentResponse(
            id=data["id"],
            filename=data["filename"],
            content=data["content"],
            checksum=data["checksum"],
        )

    if 400 <= http_response.status_code < 500:
        detail = _extract_detail(http_response, "Error al procesar el documento")
        raise HTTPException(status_code=http_response.status_code, detail=detail)

    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail=f"Error al subir documento: {http_response.text}",
    )


def _extract_detail(response: httpx.Response, default: str) -> str:
    try:
        payload = response.json()
    except ValueError:
        return default
    if isinstance(payload, dict) and "detail" in payload:
        return str(payload["detail"])
    return default


@router.get("/", response_model=list[DocumentResponse])
async def list_documents():
    """Lista todos los documentos desde el microservicio storage."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{settings.storage_url}/api/v1/documents/", timeout=10.0
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Error al listar documentos: {str(e)}",
            )

    return response.json()


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: str):
    """Obtiene un documento por su id desde el microservicio storage."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{settings.storage_url}/api/v1/documents/{document_id}", timeout=10.0
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
                detail=f"Error al obtener documento: {str(e)}",
            )
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Error al obtener documento: {str(e)}",
            )

    return response.json()


@router.put("/{document_id}", response_model=DocumentResponse)
async def update_document(document_id: str, body: UpdateDocumentRequest):
    """Actualiza el contenido de un documento en el microservicio storage."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.put(
                f"{settings.storage_url}/api/v1/documents/{document_id}",
                json={"content": body.content},
                timeout=10.0,
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
async def delete_document(document_id: str):
    """Elimina un documento por su id desde el microservicio storage."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.delete(
                f"{settings.storage_url}/api/v1/documents/{document_id}", timeout=10.0
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
                detail=f"Error al eliminar documento: {str(e)}",
            )
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Error al eliminar documento: {str(e)}",
            )