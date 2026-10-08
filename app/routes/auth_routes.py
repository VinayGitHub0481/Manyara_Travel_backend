from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.user import UserCreate, UserLogin, UserOut, Token
from app.services import auth_service
from app.core.deps import get_current_user, require_admin
from app.models.user import User,RoleEnum

from datetime import datetime,timezone 

from app.schemas.password_reset import (
    ForgotPasswordRequest,
    VerifyResetCodeRequest,
    VerifyResetCodeResponse,
    ResetPasswordRequest,
    PasswordResetResponse,
)

from app.services.password_reset_service import (
    forgot_password,
    verify_reset_code,
    reset_password,
)

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserOut)
def register(
    payload: UserCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Only an existing admin can create new users (admin or creator)."""
    return auth_service.register_user(db, payload)


@router.post("/login", response_model=Token)
def login(
    payload: UserLogin,
    db: Session = Depends(get_db),
):
    user, token = auth_service.authenticate_user(db, payload)

    # Start the 30-minute inactivity period
    if user.role in (RoleEnum.admin, RoleEnum.creator):
        user.last_activity_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(user)

    return Token(
        access_token=token,
        user=UserOut.model_validate(user),
    )



@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post(
    "/forgot-password",
    response_model=PasswordResetResponse,
)
def forgot_password_endpoint(
    payload: ForgotPasswordRequest,
    db: Session = Depends(get_db),
):
    forgot_password(
        db=db,
        payload=payload,
    )

    return {
        "message": (
            "If an account exists for this email, " "a verification code has been sent."
        )
    }


@router.post(
    "/verify-reset-code",
    response_model=VerifyResetCodeResponse,
)
def verify_reset_code_endpoint(
    payload: VerifyResetCodeRequest,
    db: Session = Depends(get_db),
):
    reset_token = verify_reset_code(
        db=db,
        payload=payload,
    )

    return {
        "message": "Verification code verified successfully.",
        "reset_token": reset_token,
    }


@router.post(
    "/reset-password",
    response_model=PasswordResetResponse,
)
def reset_password_endpoint(
    payload: ResetPasswordRequest,
    db: Session = Depends(get_db),
):
    reset_password(
        db=db,
        payload=payload,
    )

    return {"message": "Password reset successfully."}



