"""Authentication and user management endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from .. import schemas
from ..dependencies import require_admin
from ..store import fake_db


router = APIRouter(prefix="", tags=["Auth"])


@router.post("/auth/login", response_model=schemas.TokenResponse)
def login(payload: schemas.LoginRequest) -> schemas.TokenResponse:
    user = fake_db.validate_user(payload.username, payload.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = fake_db.issue_token(user_id=user["id"])
    return schemas.TokenResponse(access_token=token["token"])


@router.post("/auth/logout")
def logout(payload: schemas.LogoutRequest) -> dict:
    fake_db.revoke_token(payload.token)
    return {"status": "ok"}


@router.post("/auth/refresh", response_model=schemas.TokenResponse)
def refresh(payload: schemas.RefreshRequest) -> schemas.TokenResponse:
    existing = fake_db.tokens.get(payload.token)
    if not existing:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalid")
    fake_db.revoke_token(payload.token)
    new_token = fake_db.issue_token(existing["user_id"])
    return schemas.TokenResponse(access_token=new_token["token"])


@router.get("/users", response_model=list[schemas.UserResponse])
def list_users(_: str = Depends(require_admin)) -> list[schemas.UserResponse]:
    return [schemas.UserResponse(**user) for user in fake_db.users.values()]


@router.post("/users", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(payload: schemas.UserCreate, _: str = Depends(require_admin)) -> schemas.UserResponse:
    data = fake_db.add_user(payload.dict(exclude={"password"}))
    return schemas.UserResponse(**data)


@router.get("/users/{user_id}", response_model=schemas.UserResponse)
def get_user(user_id: str, _: str = Depends(require_admin)) -> schemas.UserResponse:
    if user_id not in fake_db.users:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return schemas.UserResponse(**fake_db.users[user_id])


@router.put("/users/{user_id}", response_model=schemas.UserResponse)
def update_user(user_id: str, payload: schemas.UserUpdate, _: str = Depends(require_admin)) -> schemas.UserResponse:
    if user_id not in fake_db.users:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    updated = fake_db.update_user(user_id, payload.dict(exclude_unset=True))
    return schemas.UserResponse(**updated)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: str, _: str = Depends(require_admin)) -> None:
    fake_db.delete_user(user_id)


@router.patch("/users/{user_id}/role", response_model=schemas.UserResponse)
def update_user_role(user_id: str, payload: schemas.RoleUpdateRequest, _: str = Depends(require_admin)) -> schemas.UserResponse:
    if user_id not in fake_db.users:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    updated = fake_db.update_user(user_id, {"role": payload.role})
    return schemas.UserResponse(**updated)
