"""Password-protected API documentation routes."""

import secrets
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from app.api.deps import get_app_settings
from app.config.settings import AppSettings

router = APIRouter()
security = HTTPBasic()


def verify_docs_credentials(
    credentials: Annotated[HTTPBasicCredentials, Depends(security)],
    settings: Annotated[AppSettings, Depends(get_app_settings)],
) -> None:
    """Validate documentation credentials with constant-time comparison."""
    valid_username = secrets.compare_digest(credentials.username, settings.docs_username)
    valid_password = secrets.compare_digest(credentials.password, settings.docs_password.get_secret_value())
    if not (valid_username and valid_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid documentation credentials",
            headers={"WWW-Authenticate": "Basic"},
        )


@router.get("/docs", include_in_schema=False)
async def swagger_docs(_: Annotated[None, Depends(verify_docs_credentials)], request: Request) -> HTMLResponse:
    """Serve password-protected Swagger UI."""
    return get_swagger_ui_html(openapi_url="/openapi.json", title=f"{request.app.title} - Swagger UI")


@router.get("/redoc", include_in_schema=False)
async def redoc_docs(_: Annotated[None, Depends(verify_docs_credentials)], request: Request) -> HTMLResponse:
    """Serve password-protected ReDoc."""
    return get_redoc_html(openapi_url="/openapi.json", title=f"{request.app.title} - ReDoc")


@router.get("/openapi.json", include_in_schema=False)
async def openapi_schema(_: Annotated[None, Depends(verify_docs_credentials)], request: Request) -> JSONResponse:
    """Serve the OpenAPI schema behind the same credentials as docs."""
    return JSONResponse(request.app.openapi())
