"""Branding configuration endpoints."""
from __future__ import annotations

from fastapi import APIRouter

from .. import schemas
from ..store import fake_db


router = APIRouter(prefix="", tags=["Branding"])


@router.get("/branding", response_model=schemas.BrandingConfig)
def get_branding() -> schemas.BrandingConfig:
    data = fake_db.branding
    return schemas.BrandingConfig(
        organization=data["organization"],
        primary_color=data["primary_color"],
        logo_url=data["logo_url"],
    )


@router.put("/branding", response_model=schemas.BrandingConfig)
def update_branding(payload: schemas.BrandingUpdateRequest) -> schemas.BrandingConfig:
    data = fake_db.branding
    for field, value in payload.dict(exclude_unset=True).items():
        data[field] = value
    return get_branding()


@router.get("/branding/template", response_model=schemas.BrandingTemplate)
def get_template() -> schemas.BrandingTemplate:
    template = fake_db.branding.get("template", {"header": "", "footer": ""})
    return schemas.BrandingTemplate(**template)


@router.put("/branding/template", response_model=schemas.BrandingTemplate)
def update_template(payload: schemas.BrandingTemplateUpdate) -> schemas.BrandingTemplate:
    template = fake_db.branding.setdefault("template", {"header": "", "footer": ""})
    for field, value in payload.dict(exclude_unset=True).items():
        template[field] = value
    return schemas.BrandingTemplate(**template)
