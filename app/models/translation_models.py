"""
Translation request and response models.
"""
from pydantic import BaseModel, Field


class TranslateRequest(BaseModel):
    """Request model for translation endpoint"""
    text: str = Field(
        ...,
        description="Japanese text to translate",
        min_length=1,
        max_length=1000,
        example="日本語の文章"
    )


class TranslateResponse(BaseModel):
    """Response model for translation endpoint."""
    translation: str = Field(
        ...,
        description="English translated text",
        example="English translated text"
    )


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str = Field(
        ...,
        description="Error message",
        example="An error occurred during translation"
    )
    detail: str | None = Field(
        None,
        description="Detailed error information",
        example="Model loading failed"
    )
