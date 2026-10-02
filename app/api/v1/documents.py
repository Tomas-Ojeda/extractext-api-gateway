import httpx
from fastapi import APIRouter, HTTPException, UploadFile, File, status
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


@router.post("/", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(file: UploadFile = File(...)):
    """Recibe un PDF, lo envía al extractor y luego al storage."""
    file_bytes = await file.read()

    # 1. Extraer texto usando el microservicio extractor
    async with httpx.AsyncClient() as client:
        try:
            extract_response = await client.post(
                f"{settings.extractor_url}/api/v1/extract",
                files={"file": (file.filename, file_bytes, "application/pdf")},
                timeout=30.0,
            )
            extract_response.raise_for_status()
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Error al extraer texto: {str(e)}",
            )

    extracted_data = extract_response.json()

    # 2. Guardar en el microservicio storage
    async with httpx.AsyncClient() as client:
        try:
            storage_response = await client.post(
                f"{settings.storage_url}/documents/",
                json={
                    "filename": file.filename or "",
                    "content": extracted_data["content"],
                    "checksum": extracted_data["checksum"],
                },
                timeout=10.0,
            )
            storage_response.raise_for_status()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 409:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="El documento ya existe (checksum duplicado)",
                )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Error al guardar documento: {str(e)}",
            )
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Error al guardar documento: {str(e)}",
            )

    return storage_response.json()


@router.get("/", response_model=list[DocumentResponse])
async def list_documents():
    """Lista todos los documentos desde el microservicio storage."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{settings.storage_url}/documents/", timeout=10.0)
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
                f"{settings.storage_url}/documents/{document_id}", timeout=10.0
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
                f"{settings.storage_url}/documents/{document_id}",
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
                f"{settings.storage_url}/documents/{document_id}", timeout=10.0
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
