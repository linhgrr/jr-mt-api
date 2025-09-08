"""
Translation API router.
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse

from ..models.translation_models import TranslateRequest, TranslateResponse, ErrorResponse
from ..services.orchestrator import translation_orchestrator
from ..core.config import get_settings

router = APIRouter(prefix="/api/v1", tags=["translation"])


def get_translation_orchestrator():
    """Dependency to get translation orchestrator."""
    return translation_orchestrator


@router.post(
    "/translate",
    response_model=TranslateResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    },
    summary="Translate Japanese text to English",
    description="Translate Japanese railway-related text to English with entity handling"
)
async def translate_text(
    request: TranslateRequest,
    orchestrator=Depends(get_translation_orchestrator),
    settings=Depends(get_settings)
):
    """
    Translate Japanese text to English.
    
    This endpoint handles Japanese railway announcements and translates them to English
    while properly handling railway entities like station names and line names.
    """
    try:
        # Validate input length
        if len(request.text) > settings.max_text_length:
            raise HTTPException(
                status_code=400,
                detail=f"Text too long. Maximum length is {settings.max_text_length} characters."
            )
        
        # Perform translation
        translation_result = await orchestrator.translate(request.text)
        
        return TranslateResponse(translation=translation_result)
        
    except HTTPException:
        raise
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "error": "Translation failed",
                "detail": str(e) if settings.debug else "An internal error occurred"
            }
        )


@router.get(
    "/health",
    summary="Health check",
    description="Check if the translation service is healthy"
)
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "Japanese Railway Translation API"}
