"""
/auth/login — the only unauthenticated endpoint in the app besides docs.
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.auth.security import verify_password, create_access_token
from app.models.seed_data import USER_ACCOUNTS

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    profile_id: str


def _find_account_by_username(username: str):
    for account in USER_ACCOUNTS.values():
        if account.username == username:
            return account
    return None


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest) -> LoginResponse:
    account = _find_account_by_username(payload.username)

    invalid_creds = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")

    if account is None:
        raise invalid_creds
    if not verify_password(payload.password, account.password_hash):
        raise invalid_creds

    token = create_access_token(user_id=account.id, role=account.role.value, profile_id=account.profile_id)
    return LoginResponse(access_token=token, role=account.role.value, profile_id=account.profile_id)