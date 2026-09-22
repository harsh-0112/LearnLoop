from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.concept import ConceptExtractionResult, ConceptRead
from app.services.concept_extraction import ConceptExtractionError, extract_concepts_from_text
from app.services.concept_ingest import persist_concepts
from app.services.document_text import UnsupportedDocumentError, extract_text

router = APIRouter(prefix="/concepts", tags=["concepts"])


@router.post("/extract", response_model=ConceptExtractionResult)
async def extract_concepts(
    subject: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> ConceptExtractionResult:
    """Extract concepts from an uploaded PDF or text file and persist them."""
    content = await file.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="uploaded file is empty"
        )

    try:
        text = extract_text(content, file.filename)
    except UnsupportedDocumentError as error:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=str(error)
        ) from error

    if not text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="no text could be extracted"
        )

    try:
        extracted = extract_concepts_from_text(text, subject)
    except ConceptExtractionError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"concept extraction failed: {error}",
        ) from error

    result = persist_concepts(db, subject, extracted)
    return ConceptExtractionResult(
        subject=subject,
        filename=file.filename or "",
        created_count=result.created_count,
        reused_count=result.reused_count,
        prerequisite_edge_count=result.prerequisite_edge_count,
        concepts=[ConceptRead.model_validate(concept) for concept in result.concepts],
    )
