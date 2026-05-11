"""
Authentication Routes
Handles evaluator login, proponent login with password, and JWT tokens.
"""

import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import Submission
from app.schemas import LoginRequest, LoginResponse, MessageResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])

security = HTTPBearer()


def create_access_token(data: dict) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(hours=settings.jwt_expiration_hours)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Dependency to verify JWT token. Returns decoded payload."""
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
        email = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido",
            )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
        )


def require_evaluator(payload: dict = Depends(verify_token)) -> dict:
    """Dependency that requires evaluator role."""
    if payload.get("role") != "evaluator":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito ao avaliador",
        )
    return payload


def require_proponent(payload: dict = Depends(verify_token)) -> dict:
    """Dependency that requires proponent role."""
    if payload.get("role") != "proponent":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito ao proponente",
        )
    return payload


# ============================================================
# Evaluator Login
# ============================================================

@router.post("/login", response_model=LoginResponse)
async def login_evaluator(request: LoginRequest):
    """Authenticate the evaluator and return a JWT token."""
    if (
        request.email != settings.evaluator_email
        or request.password != settings.evaluator_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
        )

    access_token = create_access_token(
        data={"sub": request.email, "role": "evaluator"}
    )

    return LoginResponse(access_token=access_token)


# ============================================================
# Proponent Login (email + password set during submission)
# ============================================================

@router.post("/proponent-login", response_model=LoginResponse)
async def login_proponent(
    request: LoginRequest,
    db: Session = Depends(get_db),
):
    """
    Authenticate a proponent using email + password.
    The password is set when they submit their project.
    """
    email = request.email.strip().lower()

    # Find any submission with this email
    submission = (
        db.query(Submission)
        .filter(Submission.email == email)
        .filter(Submission.password_hash.isnot(None))
        .first()
    )

    if not submission:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email não encontrado. Você já submeteu um projeto?",
        )

    if not submission.verify_password(request.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Senha incorreta",
        )

    access_token = create_access_token(
        data={"sub": email, "role": "proponent"}
    )

    return LoginResponse(access_token=access_token)
